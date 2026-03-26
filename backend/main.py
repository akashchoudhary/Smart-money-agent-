"""
Smart Money Intelligence Platform — FastAPI entry point.
"""
import logging
import time
from contextlib import asynccontextmanager

# Patch Python's SSL to use the native macOS/Windows/Linux trust store.
# Required when running behind corporate proxies (e.g. Zscaler) that
# install their own CA into the OS keychain but not into certifi's bundle.
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from api.routes import router
from database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        logger.info("→ %s %s", request.method, request.url.path)
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "← %s %s %d  %.0fms",
            request.method, request.url.path, response.status_code, duration_ms,
        )
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Smart Money Intelligence Platform …")
    try:
        await init_db()
        logger.info("Database initialized.")
    except Exception as exc:
        logger.warning("DB init skipped (running without PostgreSQL): %s", exc)

    # Pre-warm the AI model (already trained at import time, but log confirmation)
    from engines.ai_signal_engine import _model
    if _model is not None:
        logger.info("XGBoost model ready.")
    else:
        logger.info("Running with heuristic AI fallback (install xgboost to enable ML model).")

    yield
    logger.info("Shutting down …")


app = FastAPI(
    title="Smart Money Intelligence Platform",
    description="Detect institutional activity: options flow, dark pools, gamma exposure, insider buying.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # lock this down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "smart-money-platform"}
