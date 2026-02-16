import asyncio
import logging
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

        logger.info("ScreenshotService initialized. Browser launched.")

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

        cached = self._cache.get(etag)
        if cached is not None:
            return cached

        disk_cached = self._get_from_disk_cache(etag)
        if disk_cached is not None:
            self._cache[etag] = disk_cached
            return disk_cached

        url_image = await self._take_screenshot_with_retry(
            url, params, etag, local_storage, attempt=0
        )

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
                return pickle.load(f)
        except Exception:
            logger.error("Unable to read URLImage from disk cache: %s", filename)
            return None

    def _write_to_disk_cache(self, url_image: URLImage, filename: str) -> None:
        path = Path(settings.file_cache_path) / filename
        try:
            with open(path, "wb") as f:
                pickle.dump(url_image, f)
        except Exception:
            logger.error("Unable to write URLImage to disk cache: %s", filename)

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
        """Delete disk cache files older than 24 hours, every hour."""
        while True:
            await asyncio.sleep(settings.disk_cache_cleanup_interval_seconds)
            try:
                now = time.time()
                cache_dir = Path(settings.file_cache_path)
                for file_path in cache_dir.iterdir():
                    if file_path.is_file():
                        try:
                            age = now - file_path.stat().st_mtime
                            if age > settings.disk_cache_expiry_seconds:
                                file_path.unlink()
                                logger.info(
                                    "Cleaned up expired cache: %s", file_path.name
                                )
                        except Exception:
                            logger.error(
                                "Unable to check/delete expired cache: %s", file_path
                            )
            except Exception:
                logger.error("Error during disk cache cleanup")
