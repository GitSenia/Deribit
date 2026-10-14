from celery import Celery

from config import settings

celery = Celery(
    "deribit",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["worker.tasks"],
)

celery.conf.update(
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "fetch-prices-every-minute": {
            "task": "worker.fetch_prices",
            "schedule": 60.0,
        },
    },
)
