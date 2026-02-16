from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DeviceType(Enum):
    MOBILE = (480, 640)
    MOBILE_LANDSCAPE = (640, 480)
    TABLET = (675, 960)
    TABLET_LANDSCAPE = (960, 750)
    DESKTOP = (1280, 1024)
    WIDE = (1920, 1080)
    QHD = (2560, 1440)
    K4 = (3840, 2160)

    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height


class ImageSizeType(Enum):
    THUMB = (320, 180)
    THUMBX2 = (640, 320)
    ORIGINAL = (0, 0)
    FULL = (0, 0)
    FULLXHALF = (0, 0)

    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height


class ImageType(Enum):
    PNG = "image/png"
    JPEG = "image/jpeg"

    def __init__(self, content_type: str):
        self._content_type = content_type

    @property
    def content_type(self) -> str:
        return self._content_type


@dataclass
class URLImageParameters:
    device_type: DeviceType = DeviceType.DESKTOP
    device_width: Optional[int] = None
    device_height: Optional[int] = None
    image_size_type: ImageSizeType = ImageSizeType.THUMB
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    image_type: ImageType = ImageType.PNG
    image_band_color: Optional[str] = None
    cache_control: str = "public, max-age=604800"
    wait_time: int = 0

    def get_device_width(self) -> int:
        if self.device_width is not None and self.device_width != 0:
            return self.device_width
        return self.device_type.width

    def get_device_height(self) -> int:
        if self.device_height is not None and self.device_height != 0:
            return self.device_height
        return self.device_type.height

    def get_image_width(self) -> int:
        if self.image_width is not None and self.image_width != 0:
            return self.image_width
        return self.image_size_type.width

    def get_image_height(self) -> int:
        if self.image_height is not None and self.image_height != 0:
            return self.image_height
        return self.image_size_type.height

    def cache_hash(self) -> int:
        """Replicate Java URLImageParameters.hashCode() exactly.

        Java code:
            Object[] values = { deviceType.toString().hashCode(), deviceWidth, deviceHeight,
                    imageSizeType.toString().hashCode(), imageWidth, imageHeight,
                    imageType.toString().hashCode(), imageBandColor, cacheControl };
            return Objects.hash(values);

        Note: Java uses raw field values (deviceWidth, not getDeviceWidth()) in the hash.
        The toString() on Java enums returns the constant name (e.g. "DESKTOP").
        """
        return _java_objects_hash(
            _java_string_hashcode(self.device_type.name),
            self.device_width,
            self.device_height,
            _java_string_hashcode(self.image_size_type.name),
            self.image_width,
            self.image_height,
            _java_string_hashcode(self.image_type.name),
            self.image_band_color,
            self.cache_control,
        )


@dataclass
class URLImage:
    data: bytes
    url: str
    parameters: URLImageParameters
    timestamp: int  # milliseconds since epoch


def _java_string_hashcode(s: str) -> int:
    """Replicate Java's String.hashCode() as signed 32-bit int.

    Algorithm: h = 0; for ch in s: h = 31 * h + ord(ch)
    """
    h = 0
    for ch in s:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    if h >= 0x80000000:
        h -= 0x100000000
    return h


def _java_objects_hash(*values) -> int:
    """Replicate Java's Objects.hash(Object...) / Arrays.hashCode(Object[]).

    Algorithm: result = 1; for e in values: result = 31 * result + hash(e)

    For Integer: Java Integer.hashCode() returns the int value itself.
    For String: uses String.hashCode().
    For null: hash is 0.
    """
    result = 1
    for v in values:
        if v is None:
            element_hash = 0
        elif isinstance(v, int):
            # Java Integer.hashCode() returns the value, as signed 32-bit
            element_hash = v & 0xFFFFFFFF
            if element_hash >= 0x80000000:
                element_hash -= 0x100000000
        elif isinstance(v, str):
            element_hash = _java_string_hashcode(v)
        else:
            element_hash = 0
        result = ((31 * result) + element_hash) & 0xFFFFFFFF
    if result >= 0x80000000:
        result -= 0x100000000
    return result
