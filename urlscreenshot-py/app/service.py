import asyncio
import logging
import os
import pickle
import time
from pathlib import Path
from typing import Optional

from cachetools import TTLCache
from playwright.async_api import (
    Browser,
    BrowserContext,
    Playwright,
    async_playwright,
)

from app.config import settings
from app.image_service import resize_image
from app.models import ImageSizeType, URLImage, URLImageParameters
from app.validator import URL2ImageError

logger = logging.getLogger(__name__)


class ScreenshotService:
    """Manages browser lifecycle, caching, and screenshot capture."""

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._shared_context: Optional[BrowserContext] = None
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._cache: TTLCache = TTLCache(
            maxsize=settings.cache_max_size,
            ttl=settings.cache_ttl_seconds,
        )
        self._failures: TTLCache = TTLCache(
            maxsize=settings.failure_cache_max_size,
            ttl=settings.failure_cache_ttl_seconds,
        )
        self._in_flight: dict[str, asyncio.Task] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self._allowed_domains: set[str] = set()

    async def initialize(self) -> None:
        if settings.allowed_domains and settings.allowed_domains.strip():
            self._allowed_domains = set(
                d.strip()
                for d in settings.allowed_domains.split(",")
                if d.strip()
            )

        Path(settings.file_cache_path).mkdir(parents=True, exist_ok=True)

        self._semaphore = asyncio.Semaphore(settings.max_concurrent_screenshots)

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.webkit.launch()
        self._shared_context = await self._browser.new_context()

        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())

        logger.info(
            "ScreenshotService initialized. Browser launched. Allowed domains: %s",
            self._allowed_domains,
        )

    async def shutdown(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._shared_context:
            await self._shared_context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

        logger.info("ScreenshotService shut down.")

    @property
    def allowed_domains(self) -> set[str]:
        return self._allowed_domains

    async def get_screenshot(
        self,
        url: str,
        params: URLImageParameters,
        etag: str,
        local_storage: dict[str, str] | None,
        force: bool,
    ) -> URLImage:
        if force:
            self._delete_from_cache(etag)
            self._failures.pop(etag, None)

        cached = self._cache.get(etag)
        if cached is None:
            cached = self._get_from_disk_cache(etag)
            if cached is not None:
                self._cache[etag] = cached

        if cached is not None:
            if self._is_stale(cached) and etag not in self._failures:
                self._refresh_in_background(url, params, etag, local_storage)
            return cached

        failure = self._failures.get(etag)
        if failure is not None:
            raise URL2ImageError(failure)

        # Shield so a client disconnect doesn't cancel a capture others are waiting on.
        return await asyncio.shield(
            self._capture_once(url, params, etag, local_storage)
        )

    def _is_stale(self, url_image: URLImage) -> bool:
        age_ms = int(time.time() * 1000) - url_image.timestamp
        return age_ms > settings.refresh_after_seconds * 1000

    def _capture_once(
        self,
        url: str,
        params: URLImageParameters,
        etag: str,
        local_storage: dict[str, str] | None,
    ) -> asyncio.Task:
        """Return the in-flight capture for this etag, starting one if needed."""
        task = self._in_flight.get(etag)
        if task is None:
            task = asyncio.create_task(
                self._capture_and_store(url, params, etag, local_storage)
            )
            self._in_flight[etag] = task
            task.add_done_callback(lambda _: self._in_flight.pop(etag, None))
        return task

    def _refresh_in_background(
        self,
        url: str,
        params: URLImageParameters,
        etag: str,
        local_storage: dict[str, str] | None,
    ) -> None:
        if etag in self._in_flight:
            return
        logger.info("Refreshing stale URLImage in background: %s", url)
        task = self._capture_once(url, params, etag, local_storage)
        # Nobody awaits a background refresh; retrieve the exception so it isn't reported as unhandled.
        task.add_done_callback(lambda t: t.cancelled() or t.exception())

    async def _capture_and_store(
        self,
        url: str,
        params: URLImageParameters,
        etag: str,
        local_storage: dict[str, str] | None,
    ) -> URLImage:
        try:
            url_image = await self._take_screenshot_with_retry(
                url, params, etag, local_storage, attempt=0
            )
        except URL2ImageError as ex:
            self._failures[etag] = str(ex)
            raise

        self._cache[etag] = url_image
        self._write_to_disk_cache(url_image, etag)

        return url_image

    async def _take_screenshot_with_retry(
        self,
        url: str,
        params: URLImageParameters,
        etag: str,
        local_storage: dict[str, str] | None,
        attempt: int,
    ) -> URLImage:
        try:
            async with self._semaphore:
                screenshot_bytes = await self._capture_screenshot(
                    url, params, local_storage
                )
        except Exception as ex:
            logger.error(
                "Unable to take screenshot of URL: %s (attempt %d)", url, attempt
            )
            if attempt < 3:
                return await self._take_screenshot_with_retry(
                    url, params, etag, local_storage, attempt + 1
                )
            raise URL2ImageError(
                f"Unable to take screenshot of URL: {url}"
            ) from ex

        try:
            processed = resize_image(
                screenshot_bytes,
                params.image_type,
                params.get_image_width(),
                params.get_image_height(),
                params.image_band_color,
            )
        except Exception as ex:
            logger.error("Unable to resize image: %s", params)
            raise URL2ImageError(f"Unable to resize image: {params}") from ex

        return URLImage(
            data=processed,
            url=url,
            parameters=params,
            timestamp=int(time.time() * 1000),
        )

    async def _capture_screenshot(
        self,
        url: str,
        params: URLImageParameters,
        local_storage: dict[str, str] | None,
    ) -> bytes:
        """Hybrid browser strategy: tabs for non-auth, contexts for auth."""
        needs_auth = local_storage is not None

        if needs_auth:
            context = await self._browser.new_context(
                viewport={
                    "width": params.get_device_width(),
                    "height": params.get_device_height(),
                }
            )
            for key, value in local_storage.items():
                if value is not None:
                    escaped = value.replace("'", "\\'")
                    await context.add_init_script(
                        f"window.localStorage.setItem('{key}', '{escaped}');"
                    )
            page = await context.new_page()
        else:
            context = None
            page = await self._shared_context.new_page()
            await page.set_viewport_size(
                {
                    "width": params.get_device_width(),
                    "height": params.get_device_height(),
                }
            )

        try:
            page.set_default_timeout(settings.page_timeout_ms)
            page.set_default_navigation_timeout(settings.navigation_timeout_ms)

            await page.goto(url)

            if params.wait_time > 0:
                await asyncio.sleep(params.wait_time / 1000.0)

            full_page = params.image_size_type in (
                ImageSizeType.FULL,
                ImageSizeType.FULLXHALF,
            )
            return await page.screenshot(full_page=full_page)
        finally:
            await page.close()
            if needs_auth and context:
                await context.close()

    # -- Cache management --

    def _delete_from_cache(self, etag: str) -> None:
        self._cache.pop(etag, None)
        self._delete_from_disk_cache(etag)
        logger.info("Deleted URLImage with eTag: %s", etag)

    def delete_all_from_cache(self) -> None:
        self._cache.clear()
        self._delete_all_from_disk_cache()
        logger.info("Deleted all URLImages")

    def _get_from_disk_cache(self, filename: str) -> Optional[URLImage]:
        path = Path(settings.file_cache_path) / filename
        if not path.exists():
            return None
        try:
            with open(path, "rb") as f:
                url_image = pickle.load(f)
            # mtime tracks last access; cleanup evicts by it.
            os.utime(path)
            return url_image
        except Exception:
            logger.error("Unable to read URLImage from disk cache: %s", filename)
            return None

    def _write_to_disk_cache(self, url_image: URLImage, filename: str) -> None:
        path = Path(settings.file_cache_path) / filename
        tmp_path = path.with_name(f".{filename}.tmp")
        try:
            # Write then rename so a concurrent read never sees a partial file.
            with open(tmp_path, "wb") as f:
                pickle.dump(url_image, f)
            os.replace(tmp_path, path)
        except Exception:
            logger.error("Unable to write URLImage to disk cache: %s", filename)
            tmp_path.unlink(missing_ok=True)

    def _delete_from_disk_cache(self, filename: str) -> None:
        path = Path(settings.file_cache_path) / filename
        try:
            path.unlink(missing_ok=True)
        except Exception:
            logger.error("Unable to delete URLImage from disk cache: %s", filename)

    def _delete_all_from_disk_cache(self) -> None:
        cache_dir = Path(settings.file_cache_path)
        try:
            for file_path in cache_dir.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                    except Exception:
                        logger.error("Unable to delete: %s", file_path)
        except Exception:
            logger.error("Unable to delete all URLImages from disk cache")

    async def _periodic_cleanup(self) -> None:
        while True:
            await asyncio.sleep(settings.disk_cache_cleanup_interval_seconds)
            try:
                self._cleanup_disk_cache()
            except Exception:
                logger.error("Error during disk cache cleanup", exc_info=True)

    def _cleanup_disk_cache(self) -> None:
        """Evict files not accessed within the expiry window, then least recently
        used files until the cache fits within the size limit."""
        now = time.time()
        kept: list[tuple[float, int, Path]] = []
        for file_path in Path(settings.file_cache_path).iterdir():
            if not file_path.is_file():
                continue
            try:
                stat = file_path.stat()
                if now - stat.st_mtime > settings.disk_cache_expiry_seconds:
                    file_path.unlink()
                    logger.info("Evicted unused cache: %s", file_path.name)
                else:
                    kept.append((stat.st_mtime, stat.st_size, file_path))
            except Exception:
                logger.error("Unable to check/delete cache file: %s", file_path)

        total = sum(size for _, size, _ in kept)
        if total <= settings.disk_cache_max_bytes:
            return

        kept.sort(key=lambda entry: entry[0])
        for _, size, file_path in kept:
            if total <= settings.disk_cache_max_bytes:
                break
            try:
                file_path.unlink()
                total -= size
                logger.info("Evicted cache over size limit: %s", file_path.name)
            except Exception:
                logger.error("Unable to delete cache file: %s", file_path)
