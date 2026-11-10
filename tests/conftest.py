from contextlib import asynccontextmanager

import pytest
from fastapi.testclient import TestClient

from app import db
from app import main


class FakeConnection:
    def __init__(self):
        self.user_id = 1
        self.order_id = 1

    async def execute(self, query):
        return "CREATE TABLE"

    async def fetch(self, query):
        return []

    async def fetchrow(self, query, *args):
        if "orders" in query:
            row = {
                "id": self.order_id,
                "customer_email": args[0],
                "item": args[1],
                "quantity": args[2],
                "amount_cents": args[3],
            }
            self.order_id += 1
            return row
        if "WHERE id" in query:
            return None
        row = {"id": self.user_id, "name": args[0], "email": args[1]}
        self.user_id += 1
        return row


class FakePool:
    def __init__(self):
        self.connection = FakeConnection()

    @asynccontextmanager
    async def acquire(self):
        yield self.connection

    def get_size(self):
        return 2

    async def close(self):
        return None


@pytest.fixture
def client(monkeypatch):
    fake_pool = FakePool()

    async def noop():
        return None

    monkeypatch.setattr(main, "init_pool", noop)
    monkeypatch.setattr(main, "ensure_tables", noop)
    monkeypatch.setattr(main, "close_pool", noop)
    monkeypatch.setattr(db.pool, "pool", fake_pool)
    with TestClient(main.app) as test_client:
        yield test_client
