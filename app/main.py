from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.db.pool import init_pool, close_pool
from app.db.init_db import ensure_tables
from app.routes.user import router as user_router


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


@app.get("/health")
async def health_check():
    return {"status": "ok"}