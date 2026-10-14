from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.prices import router
from app.db.base import get_db

app = FastAPI()
app.include_router(router, prefix="/api/v1")


async def _fake_db():
    yield AsyncMock()


app.dependency_overrides[get_db] = _fake_db
client = TestClient(app)


def test_prices_ok():
    with patch(
        "app.api.v1.endpoints.prices.get_all_prices",
        new_callable=AsyncMock,
        return_value=[],
    ):
        response = client.get("/api/v1/prices?ticker=btc_usd")

    assert response.status_code == 200
    assert response.json() == []


def test_latest_404():
    with patch(
        "app.api.v1.endpoints.prices.get_latest_price",
        new_callable=AsyncMock,
        return_value=None,
    ):
        response = client.get("/api/v1/prices/latest?ticker=btc_usd")

    assert response.status_code == 404


def test_ticker_required():
    response = client.get("/api/v1/prices")
    assert response.status_code == 422
