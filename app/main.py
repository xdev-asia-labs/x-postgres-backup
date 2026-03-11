"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.database import get_db, init_db
from app.i18n import (
    DEFAULT_LANGUAGE,
    LANGUAGE_COOKIE,
    LANGUAGE_NAMES,
    SUPPORTED_LANGUAGES,
    get_lang_from_request,
    make_translate_func,
)
from app.routers import api, auth, dashboard
from app.scheduler import start_scheduler, stop_scheduler
from app.services.auth import ensure_default_admin

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s...", settings.APP_NAME)
    init_db()

    # Create default admin user if not exists
    db = next(get_db())
    try:
        ensure_default_admin(db)
    finally:
        db.close()

    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Register i18n globals for Jinja2
templates.env.globals["SUPPORTED_LANGUAGES"] = SUPPORTED_LANGUAGES
templates.env.globals["LANGUAGE_NAMES"] = LANGUAGE_NAMES
templates.env.globals["DEFAULT_LANGUAGE"] = DEFAULT_LANGUAGE

app.state.templates = templates

# Static files
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.middleware("http")
async def i18n_middleware(request: Request, call_next):
    """Inject i18n translation function into request state for all routes."""
    lang = get_lang_from_request(request)
    request.state.lang = lang
    request.state._ = make_translate_func(lang)
    response = await call_next(request)
    return response


@app.get("/set-language/{lang}")
async def set_language(lang: str, request: Request):
    """Set the user's preferred language via cookie."""
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    referer = request.headers.get("referer", "/")
    response = RedirectResponse(url=referer, status_code=303)
    response.set_cookie(
        key=LANGUAGE_COOKIE,
        value=lang,
        max_age=365 * 24 * 3600,  # 1 year
        httponly=False,
        samesite="lax",
    )
    return response


# Routers
app.include_router(auth.router)
app.include_router(api.router)
app.include_router(dashboard.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.debug,
    )
