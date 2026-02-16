import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import router
from app.service import ScreenshotService


def _configure_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    log_file = f"/logs/ehcache-{settings.instance_id}.log"
    try:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    except Exception:
        pass

    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_logging()
    service = ScreenshotService()
    await service.initialize()
    app.state.screenshot_service = service
    yield
    await service.shutdown()


app = FastAPI(title="URL Screenshot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_credentials=False,
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/actuator/health")
async def health():
    return {"status": "UP"}
