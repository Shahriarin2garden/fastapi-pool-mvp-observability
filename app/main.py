from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging
import time
from prometheus_fastapi_instrumentator import Instrumentator
from app.db.pool import init_pool, close_pool
from app.db.init_db import ensure_tables
from app.routes.user import router as user_router
from app.routes.orders import router as orders_router
from app.monitoring.metrics import db_pool_max_size
from app.monitoring.metrics import order_request_duration, order_requests_total


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        print("Initializing database pool...")
        await init_pool()
        print("Creating database tables...")
        await ensure_tables()
        print("Application startup completed successfully")
    except Exception as e:
        print(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        print("Closing database pool...")
        await close_pool()
        print("Application shutdown completed")
    except Exception as e:
        print(f"Shutdown error: {e}")
        raise


app = FastAPI(
    title="FastAPI Pool MVP",
    description="A minimal FastAPI application with asyncpg connection pooling",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(user_router)
app.include_router(orders_router)


@app.middleware("http")
async def order_metrics_middleware(request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    if request.method == "POST" and request.url.path == "/api/orders":
        status_class = f"{response.status_code // 100}xx"
        order_requests_total.labels(status_class).inc()
        order_request_duration.observe(time.perf_counter() - started)
    return response


# Initialize Prometheus instrumentation
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app)

@app.get("/health")
async def health_check():
    return {"status": "ok"}