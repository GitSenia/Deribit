# Deribit Price Service

Сервис собирает index price `btc_usd` и `eth_usd` с биржи [Deribit](https://docs.deribit.com) раз в минуту, сохраняет в PostgreSQL и отдаёт данные через FastAPI.

## Стек

- Python, FastAPI, SQLAlchemy (async) + asyncpg
- Celery + Redis (периодический сбор цен)
- aiohttp (клиент Deribit)
- PostgreSQL
- Docker Compose

## Структура

```
Deribit/
├── docker-compose.yml      # db, redis, api, worker
├── pytest.ini
├── deribit/
│   ├── app/                # FastAPI: API, БД, сервисы
│   ├── worker/             # Celery: задачи и beat
│   ├── config.py
│   ├── logger.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── test/
└── .env                    # локальные настройки (не в git)
```

## Быстрый старт (Docker)

Нужны Docker и Docker Compose.

1. Создай `.env` в корне (можно скопировать значения ниже):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prices
DB_USER=postgres
DB_PASSWORD=postgres
REDIS_URL=redis://localhost:6379/0
DERIBIT_API_BASE=https://www.deribit.com/api/v2
TICKERS=btc_usd,eth_usd
APP_NAME=deribit-price-service
LOG_LEVEL=INFO
```

2. Запуск:

```bash
docker compose up --build
```

Сервисы:
- `db` — PostgreSQL
- `redis` — брокер Celery
- `api` — FastAPI (`http://localhost:8000`)
- `worker` — Celery worker + beat (опрос раз в минуту)

3. Проверка:

- Health: http://localhost:8000/health  
- Swagger: http://localhost:8000/docs  

Подожди ~1 минуту после старта, чтобы worker успел записать первые цены.

Остановка:

```bash
docker compose down
```

## Локальный запуск (без Docker для API)

Нужны запущенные PostgreSQL и Redis, Python 3.11+.

```bash
cd deribit
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```

В корне проекта должен быть `.env` (см. выше). Для локального запуска `DB_HOST=localhost`, `REDIS_URL=redis://localhost:6379/0`.

Терминал 1 — API:

```bash
cd deribit
uvicorn app.main:app --reload
```

Терминал 2 — Celery:

```bash
cd deribit
celery -A worker.celery_app.celery worker --beat --loglevel=info
```

## API

Все методы — `GET`. Query-параметр `ticker` обязателен (`btc_usd` или `eth_usd`).

| Метод | Описание |
|---|---|
| `GET /api/v1/prices?ticker=btc_usd` | все сохранённые цены по тикеру |
| `GET /api/v1/prices/latest?ticker=btc_usd` | последняя цена |
| `GET /api/v1/prices/filter?ticker=eth_usd&from=1700000000&to=2000000000` | цены в диапазоне UNIX-времени |

Примеры:

```bash
curl "http://localhost:8000/api/v1/prices?ticker=btc_usd"
curl "http://localhost:8000/api/v1/prices/latest?ticker=btc_usd"
curl "http://localhost:8000/api/v1/prices/filter?ticker=eth_usd&from=1700000000&to=2000000000"
```

Пример ответа:

```json
{
  "ticker": "btc_usd",
  "price": 95000.12,
  "timestamp": 1710000000
}
```

## Тесты

Из корня репозитория:

```bash
pip install -r deribit/requirements.txt
pytest -v
```

## Design decisions

- **Отдельный worker** — Celery вынес в отдельный контейнер, а не держал вместе с FastAPI в одном процессе. API и сбор цен — разные задачи: API должен быстро отвечать клиенту, worker раз в минуту ходит на биржу и пишет в БД. Если worker упадёт или его перезапустить, API продолжит работать. Логи и нагрузку тоже проще разделять.
- **Всё асинхронно** — FastAPI, клиент Deribit (`aiohttp`) и работа с Postgres (`asyncpg` + async SQLAlchemy) сделаны async. Запросы к API и к бирже не должны блокировать процесс на ожидании сети или БД — под нагрузкой это заметно стабильнее, чем синхронный код.
- **Параллельный опрос тикеров** — в `fetch_all_tickers` используется  
  `asyncio.gather(*[_one(ticker) for ticker in settings.TICKERS])`.  
  BTC и ETH запрашиваются **одновременно**, а не по очереди. Так сбор цен быстрее: ждать нужно примерно время одного HTTP-запроса, а не сумму двух.
- **Celery + Beat** — периодичность «раз в минуту» из ТЗ закрыта beat-расписанием; API только читает уже сохранённые данные.
- **Redis** — брокер очереди для Celery (нужен, чтобы worker получал задачи).
- **Слои `app/services` и `worker`** — логика клиента и CRUD в сервисах, worker только запускает задачу и не дублирует код.

## Проблемы, с которыми столкнулся

### Celery + async SQLAlchemy: `Future attached to a different loop`

**Суть:** Celery-задача синхронная и каждый раз вызывает `asyncio.run()`, а это новый event loop. Глобальный async engine SQLAlchemy создавался при импорте и держал пул соединений от предыдущего loop. На втором и следующих запусках задачи падала ошибка: соединение уже привязано к другому loop.

**Как решил:** в задаче `fetch_prices` на каждый запуск создаётся свой `create_async_engine` с `NullPool`, после работы вызывается `dispose()`. Engine не переиспользуется между разными `asyncio.run()`.

## Что можно улучшить

Сейчас цены забираются по HTTP раз в минуту. У Deribit есть **WebSocket**-API для подписки на котировки. Если добавить поддержку WebSocket, цены можно получать почти в реальном времени, без ожидания следующего тика Celery — это будет быстрее и меньше нагрузка на REST-запросы.
