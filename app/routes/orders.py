import logging
import random
import time

import asyncpg
from fastapi import APIRouter, HTTPException, Query, Request, status

from app.config import settings
from app.db import pool as pool_module
from app.monitoring.metrics import (
    db_connection_acquire_duration,
    db_query_duration,
    db_query_errors,
    order_value_cents_total,
    orders_total,
)
from app.schemas.order_schema import OrderCreate, OrderResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    request: Request,
    simulate_failure: bool = Query(default=False),
):
    started = time.perf_counter()
    try:
        if simulate_failure or random.random() < settings.FAILURE_RATE:
            raise HTTPException(
                status_code=500, detail="simulated order processing failure"
            )
        if pool_module.pool is None:
            raise RuntimeError("database pool is not initialized")
        acquire_started = time.perf_counter()
        async with pool_module.pool.acquire() as conn:
            db_connection_acquire_duration.observe(time.perf_counter() - acquire_started)
            query_started = time.perf_counter()
            row = await conn.fetchrow(
                """
                INSERT INTO orders (customer_email, item, quantity, amount_cents)
                VALUES ($1, $2, $3, $4)
                RETURNING id, customer_email, item, quantity, amount_cents
                """,
                str(order.customer_email),
                order.item,
                order.quantity,
                order.amount_cents,
            )
            db_query_duration.observe(time.perf_counter() - query_started)
        orders_total.labels("success").inc()
        order_value_cents_total.inc(order.amount_cents)
        result = OrderResponse(**dict(row), status="created")
        logger.info(
            "level=INFO event=order_created order_id=%s item=%s quantity=%s duration_ms=%.1f trace_id=%s",
            result.id,
            result.item,
            result.quantity,
            (time.perf_counter() - started) * 1000,
            request.state.trace_id,
        )
        return result
    except HTTPException:
        orders_total.labels("failed").inc()
        logger.error(
            "level=ERROR event=order_failed reason=simulated duration_ms=%.1f trace_id=%s",
            (time.perf_counter() - started) * 1000,
            request.state.trace_id,
        )
        raise
    except (asyncpg.PostgresError, RuntimeError):
        db_query_errors.inc()
        orders_total.labels("failed").inc()
        logger.error(
            "level=ERROR event=order_failed reason=database duration_ms=%.1f trace_id=%s",
            (time.perf_counter() - started) * 1000,
            request.state.trace_id,
        )
        raise HTTPException(status_code=503, detail="order service unavailable")
