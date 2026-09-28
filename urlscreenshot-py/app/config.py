from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 6201
    instance_id: str = "default"

    allowed_domains: str = ""

    file_cache_path: str = "/tmp/ehcache"

    cache_max_size: int = 100
    cache_ttl_seconds: int = 3600

    # Disk files are evicted by last access, not by age of the screenshot.
    disk_cache_expiry_seconds: int = 2592000
    disk_cache_max_bytes: int = 2 * 1024 * 1024 * 1024
    disk_cache_cleanup_interval_seconds: int = 3600

    # Cached screenshots older than this are served as-is and retaken in the background.
    refresh_after_seconds: int = 21600

    # Failed captures are remembered so dead sites aren't retried on every request.
    failure_cache_ttl_seconds: int = 600
    failure_cache_max_size: int = 1000

    max_concurrent_screenshots: int = 6

    page_timeout_ms: int = 30000
    navigation_timeout_ms: int = 30000


settings = Settings()
