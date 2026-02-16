from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 6201
    instance_id: str = "default"

    allowed_domains: str = ""

    file_cache_path: str = "/tmp/ehcache"

    cache_max_size: int = 100
    cache_ttl_seconds: int = 3600

    disk_cache_expiry_seconds: int = 86400
    disk_cache_cleanup_interval_seconds: int = 3600

    max_concurrent_screenshots: int = 6

    page_timeout_ms: int = 30000
    navigation_timeout_ms: int = 30000


settings = Settings()
