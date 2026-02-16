import logging
import time
import traceback

from fastapi import APIRouter, Request, Response

from app.models import (
    DeviceType,
    ImageSizeType,
    ImageType,
    URLImageParameters,
    _java_string_hashcode,
)
from app.service import ScreenshotService
from app.validator import URL2ImageError, validate_and_get_url, validate_referrer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/url2image")


def _get_service(request: Request) -> ScreenshotService:
    return request.app.state.screenshot_service


def _parse_params(request: Request) -> URLImageParameters:
    params = URLImageParameters()

    if device_type := request.query_params.get("deviceType"):
        params.device_type = DeviceType[device_type.upper()]

    if device_width := request.query_params.get("deviceWidth"):
        params.device_width = int(device_width)

    if device_height := request.query_params.get("deviceHeight"):
        params.device_height = int(device_height)

    if image_size_type := request.query_params.get("imageSizeType"):
        params.image_size_type = ImageSizeType[image_size_type.upper()]

    if image_width := request.query_params.get("imageWidth"):
        params.image_width = int(image_width)

    if image_height := request.query_params.get("imageHeight"):
        params.image_height = int(image_height)

    if image_type := request.query_params.get("imageType"):
        params.image_type = ImageType[image_type.upper()]

    if image_band_color := request.query_params.get("imageBandColor"):
        params.image_band_color = image_band_color

    if cache_control := request.query_params.get("cacheControl"):
        params.cache_control = cache_control

    if wait_time := request.query_params.get("waitTime"):
        params.wait_time = int(wait_time)

    return params


def _compute_etag(url: str, params: URLImageParameters) -> str:
    """Replicate Java: url.hashCode() + "-" + params.hashCode()"""
    return f"{_java_string_hashcode(url)}-{params.cache_hash()}"


@router.get("/{path:path}")
async def get_screenshot(request: Request):
    service = _get_service(request)

    try:
        validate_referrer(service.allowed_domains, request.headers.get("referer"))

        url = validate_and_get_url(request.url.path, "url2image")
        params = _parse_params(request)

        logger.debug("Request params: %s - hashCode: %s", params, params.cache_hash())

        etag = _compute_etag(url, params)

        if_none_match = request.headers.get("if-none-match")
        force = request.query_params.get("force") is not None

        local_storage = None
        auth_header = request.headers.get("authorization")
        if auth_header is not None:
            auth_token = auth_header
            if not auth_token.startswith('"') or not auth_token.endswith('"'):
                auth_token = f'"{auth_token}"'
            local_storage = {
                "AuthToken": auth_token,
                "AuthTokenExpiry": request.headers.get("authtokenexpiry"),
            }

        url_image = await service.get_screenshot(
            url, params, etag, local_storage, force
        )

        if (
            if_none_match is not None
            and if_none_match.startswith(etag)
            and if_none_match.endswith(str(url_image.timestamp))
        ):
            return Response(status_code=304)

        headers = {
            "Cache-Control": params.cache_control,
            "Content-Type": params.image_type.content_type,
            "X-Cache": "MISS"
            if (int(time.time() * 1000) - url_image.timestamp) < 300
            else "HIT",
        }

        if "must-revalidate" in params.cache_control:
            headers["ETag"] = f"{etag}-{url_image.timestamp}"

        return Response(
            content=url_image.data,
            media_type=params.image_type.content_type,
            headers=headers,
        )

    except URL2ImageError as e:
        logger.error("Error in get_screenshot: %s", e)
        return Response(content=str(e), status_code=e.status_code)
    except Exception as e:
        logger.error("Error while creating screenshot: %s", e, exc_info=True)
        return Response(content=traceback.format_exc(), status_code=500)


@router.delete("/internal/all")
async def delete_all(request: Request):
    """Must be registered BEFORE the catch-all delete route."""
    service = _get_service(request)
    try:
        service.delete_all_from_cache()
        return Response(status_code=200)
    except Exception as e:
        logger.error("Error while deleting everything in cache: %s", e, exc_info=True)
        return Response(content=traceback.format_exc(), status_code=500)


@router.delete("/{path:path}")
async def delete_screenshot(request: Request):
    service = _get_service(request)
    try:
        url = validate_and_get_url(request.url.path, "url2image")
        params = _parse_params(request)
        etag = _compute_etag(url, params)
        service._delete_from_cache(etag)
        return Response(status_code=200)
    except Exception as e:
        logger.error("Error while deleting from cache: %s", e, exc_info=True)
        return Response(content=traceback.format_exc(), status_code=500)
