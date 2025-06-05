# 📖 Bookstore Backend

A full‐featured, Dockerized Flask backend for a bookstore, complete with:

- **JWT Authentication** (login, registration, refresh, user profile)
- **Book Management** (CRUD for admins; public listings for users)
- **AI‐Powered Summaries** (via OpenAI / Cohere API)
- **Category & Reviews** (users can submit and view reviews)
- **Cart & Order Processing** (cart persistence, order placement, status tracking)
- **Async Inventory** (RabbitMQ‐driven stock updates, decoupled workers)
- **Real‐Time Notifications** (Flask‐SocketIO + RabbitMQ for live order updates)
- **OpenAPI Docs** (powered by Flask‐Smorest & Marshmallow schemas)
- **Docker & Docker Compose** (dev/prod setups under `infra/`)

Feel free to explore the source code, experiment locally, or deploy to production using the provided Docker configurations.

---

## 📄 Table of Contents

1. [Features](#features)
2. [Directory Structure](#directory-structure)
3. [Quick Start (Local Development)](#quick-start-local-development)
4. [Production Deployment](#production-deployment)
5. [API Reference](#api-reference)
   - [Authentication Endpoints](#authentication-endpoints)
   - [Books Endpoints](#books-endpoints)
   - [Orders Endpoints](#orders-endpoints)
6. [Database Seeding](#database-seeding)
7. [WebSocket & Messaging](#websocket--messaging)
8. [Running Tests](#running-tests)
9. [Contributing](#contributing)
10. [License](#license)
11. [Design Decisions & AI Integration](#design-decisions--ai-integration)

---

## 🌐 Features

- **OpenAPI / Swagger** documentation via Flask‐Smorest (see `/api/spec` or `/api/docs` in dev).
- **JWT‐based Authentication**
  - Registration, Login, Token Refresh
  - Protected “me” endpoint to fetch user info
- **Book Management**
  - Admins can create, update, soft‐delete, and un‐delete books
  - Public can view active books, categories, and summaries
- **AI‐Powered Summaries**
  - On `GET /api/books/{book_id}/summary`, the system either returns a cached summary or uses OpenAI/Cohere to generate one
- **Category & Reviews**
  - Books grouped into categories (e.g. Fiction, Non‐Fiction)
  - Authenticated users can post and fetch reviews per book
- **Cart & Order Flow**
  1. Users add books to a cart (stored in DB).
  2. On `/api/orders`, an order is created with `OrderItems`.
  3. Order status transitions: `PENDING → PAID → SHIPPED → DELIVERED → CANCELLED / REFUNDED`.
  4. After order creation, RabbitMQ messages decouple stock updates and notifications.
- **Async Inventory Processing**
  - A background consumer (`app/inventory/consumer.py`) listens to an `order_created` queue, decrements stock, emits WebSocket events, and updates order status.
- **Real‐Time WebSocket Notifications**
  - Using Flask‐SocketIO (with `message_queue=RabbitMQ`) so that multiple workers can broadcast updates.
  - Clients (frontend SPA) can subscribe to `order_update` events.
- **Docker + Docker Compose**
  - Separate `infra/dev/` and `infra/prod/` setups for local development vs. production deployment.
  - Pre‐configured Dockerfiles, Compose files, and entrypoint scripts to bring up Postgres, RabbitMQ, web, and worker containers.
- **Idempotent Seeding**
  - `seed_all.py` creates an admin user, default categories, and books with randomized unique ISBNs—safe to run on every startup.
- **Testing**
  - Pytest‐based tests under `tests/` (covering auth, books, orders, inventory).

---

## 🧱 Directory Structure

```plaintext
bookstore-backend/
├── README.md
├── DESIGN_DECISIONS.md        ← Detailed design & AI integration (link)
├── run.py                     ← Entrypoint for local dev (SocketIO)
├── seed.py                  ← Idempotent seeder (admin, categories, books)
├── requirements.txt
├── pyproject.toml
├── migrations/
│   ├── alembic.ini
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/                       # Flask application package
│   ├── __init__.py            # App factory, load_dotenv, eventlet patch
│   ├── config.py              # Config classes (Dev / Prod / Testing)
│   ├── extensions.py          # JWT, DB, SocketIO, Marshmallow, CORS, Migrate
│   ├── error_handlers.py      # Global error handlers
│   ├── health/
│   │   └── routes.py          # /api/health
│   ├── auth/
│   │   ├── models.py          # User
│   │   ├── routes.py          # /api/auth
│   │   ├── schemas.py         # Marshmallow schemas
│   │   └── permissions.py     # Custom permissions
│   ├── books/
│   │   ├── models.py          # Book, Category, Review, Summary
│   │   ├── routes.py          # /api/books endpoints
│   │   ├── schemas.py         # Marshmallow schemas
│   │   └── ai_service.py      # OpenAI / Cohere integration
│   ├── orders/
│   │   ├── enums.py           # OrderStatus enum
│   │   ├── models.py          # Order, OrderItem ...
│   │   ├── routes.py          # /api/orders & /api/cart endpoints
│   │   ├── schemas.py
│   │   └── services.py        # Business logic (cart → order)
│   ├── inventory/
│   │   ├── consumer.py        # RabbitMQ consumer to update stock & emit events
│   │   └── __init__.py
│   ├── websocket/
│   │   ├── events.py          # SocketIO event namespace (OrderNamespace)
│   │   └── __init__.py
│   ├── static/                # Frontend SPA static assets (CSS, JS)
│   ├── templates/             # SPA HTML (index.html)
│   ├── utils/
│   │   ├── blueprints.py      # Helper to define blueprints
│   │   ├── common_schema.py   # Shared Marshmallow fields
│   │   └── validations.py     # Custom validators
│   └── models/                # All models imported here
│       └── __init__.py
├── infra/
│   ├── dev/                   # Local development Docker setup
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   ├── .env
│   │   └── .flaskenv
│   ├── prod/                  # Production Docker setup
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml
│   │   └── .env
│   ├── scripts/               # Shared entrypoint scripts
│   │   ├── entrypoint.web.sh
│   │   └── entrypoint.worker.sh
│   └── services/               # Tools used in Docker
│       ├── postgres/
│       │   ├── Dockerfile
│       │   └── .postgres     # Postgres env (used only by prod compose)
│       └── rabbitmq/
│           ├── Dockerfile
│           └── .rabbitmq     # RabbitMQ env (used only by prod compose)
├── logs/                  # Runtime logs (e.g. bookstore.log) (not on repo)
```

## Quick Start (Local Development)


These instructions assume you have **Docker** & **Docker Compose** installed locally, along with **Python 3.8+** if you want to run outside Docker.

---

### 1. Clone & Enter the Repo

```bash
git clone https://github.com/emmanueldev247/bookstore-backend.git
cd bookstore-backend
```

---

### 2. Inspect (or edit) `infra/dev/.env` and `infra/dev/.flaskenv`

#### `infra/dev/.env` (development environment variables):

```ini
SECRET_KEY=***********************************
JWT_SECRET_KEY=********************************
COHERE_API_KEY==********************************
DATABASE_URL=postgresql://<username>:<password>@<host>:<port>/<database_name>
RABBITMQ_URL=amqp://<username>:<password>@<host>:<port>/<virtual_host>
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=ChangeMe123!
```

> `DATABASE_URL` refers to `postgres:5432` because the Compose service is named `postgres`.
> `RABBITMQ_URL` uses `rabbitmq:5672` similarly.

#### `infra/dev/.flaskenv`:

```ini
FLASK_APP=run.py
FLASK_ENV=development
FLASK_DEBUG=1
```

> This ensures `run.py` is used for `flask run`, and the code runs in development mode.

> You can adjust any variables (e.g. `COHERE_API_KEY`, `OPENAI_API_KEY`) as needed.

---

### 3. Build & Bring Up Containers

```bash
cd infra/dev
docker compose up --build
```

This will:

1. **Build the following images:**

    - `bookstore_postgres_dev_image` (Postgres 16)
    - `bookstore_rabbitmq_dev_image` (RabbitMQ 3-management)
    - `bookstore_web_dev_image` (Flask + dependencies)
    - `bookstore_worker_dev_image` (same base as web)

2. **Start 4 containers:**

    - **bookstore_postgres_dev**
        - DB initialized with `POSTGRES_DB=bookstore_db`
        - Named volume `pgdata_dev` holds data files

    - **bookstore_rabbitmq_dev**
        - Management UI on port **15672**
        - Named volume `rabbitdata_dev` for MQTT messages

    - **bookstore_web_dev**
        - Waits for Postgres & RabbitMQ
        - Runs `flask db upgrade` → applies migrations
        - Runs `python seed_all.py` → seeds admin, categories, books (with random ISBNs)
        - Starts Flask dev server on `0.0.0.0:5000` with hot-reload enabled

    - **bookstore_worker_dev**
        - Waits for RabbitMQ
        - Runs `python -u -m app/inventory/consumer.py` to listen for `order_created` messages

### 📜 Logs should show messages like:

```
[postgres]
[rabbitmq]
[web] Waiting for Postgres...
[web] Postgres is ready ✅
[web] Waiting for RabbitMQ...
[web] RabbitMQ is ready ✅
[web] Running migrations...
[web] Running combined seeder...
[seed_all] Created admin user: admin@example.com
[seed_all] Category Fiction already exists → skipping.
[seed_all] Created book: 'The Great Gatsby' (ISBN: 4829301923847) in category 'Fiction'
…
[web] Starting Flask dev server...
* Serving Flask app "app"
* Environment: development
* Debug mode: on
* Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)
[worker] Waiting for RabbitMQ...
[worker] RabbitMQ is ready ✅
[worker] Starting inventory consumer...
```

---

### 4. 🌐 **Browse:**

- OpenAPI/Swagger UI:
  [http://localhost:5000/api/docs](http://localhost:5000/api/docs)
  (or `/api/spec`)

- Health Check:
  [http://localhost:5000/api/health](http://localhost:5000/api/health)

- You can use Postman or `curl` to test **auth**, **books**, **orders**, etc.

---

### 5. 🛠 RabbitMQ Management (dev only)

- Visit: [http://localhost:15672](http://localhost:15672)
- Login: `guest / guest`
- View queues, exchanges, messages

---

### 6. 🧠 Database Access (dev only)

If you want to inspect Postgres, connect with any PostgreSQL client:

- Host: `localhost`
- Port: `5432`
- Username: `debug`
- Password: `debug`
- Database: `bookstore_db`

# 🚀 Production Deployment

Below is a high‐level guide to bring up a production‐style environment. In production, we bake code into the image (no volume mounts), ensure `always up` restart policies, and run **Gunicorn** instead of the Flask dev server.

---

## 📁 Environment Variables

Place your production environment variables in `infra/prod/.env`:

```ini
FLASK_ENV=production
SECRET_KEY=ab77ccd46f93661e00440fbff698588f9ea686edd7410a672d3417d8c6e1c6e4
JWT_SECRET_KEY=edbe4c81408be0367b3825b9d0d7b546eb2db82ae51035703550b9101e8a1572
DATABASE_URL=postgresql://debug:debug@postgres:5432/bookstore_db
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
COHERE_API_KEY=6kwEetHB6zyMCXbRtNC7YjvnUFiHSjkbekiBR8or
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=ChangeMe123!
```

---

## 🔧 Build & Run Production Stack

```bash
cd infra/prod
docker compose up --build -d
```

This will:

- Build `bookstore_postgres_prod_image`, `bookstore_rabbitmq_prod_image`, `bookstore_web_prod_image`, and `bookstore_worker_prod_image`.
- Start containers with `restart: unless-stopped`.
- `web` container runs:
  ```bash
  gunicorn -k eventlet -w 2 -b 0.0.0.0:5000 app:create_app()
  ```
  (Two eventlet workers, RabbitMQ used for SocketIO bridging.)
- `worker` container runs inventory consumer.

---

## ✅ Verify Deployment

```bash
docker ps
docker logs bookstore_web_prod
docker logs bookstore_worker_prod
```

Visit:
[http://<YOUR_PROD_HOST>:5000/api/health](http://<YOUR_PROD_HOST>:5000/api/health)

> If you expose RabbitMQ ports (`15672`), you can log into the management UI.
> Otherwise, it remains internal.

---

## 🌐 Networking

In production, you may want to front Gunicorn with an **Nginx** or **Traefik** reverse proxy (TLS, static assets, caching, etc.).
That’s outside the scope of this minimal setup.

---

# 🔍 API Reference

A summary of major endpoints. For request/response schemas, refer to live OpenAPI docs at `/api/docs`.

---

## 🔐 Authentication Endpoints

| Method | Endpoint           | Access       | Description                               |
|--------|--------------------|--------------|-------------------------------------------|
| POST   | `/api/auth/register` | Public     | Register a new user.                      |
| POST   | `/api/auth/login`    | Public     | Login and receive JWT tokens.            |
| POST   | `/api/auth/refresh`  | Authenticated | Refresh access token.                    |
| GET    | `/api/auth/me`       | Authenticated | Get current user profile.              |

---

## 📚 Books Endpoints

| Method | Endpoint                          | Access     | Description                                      |
|--------|-----------------------------------|------------|--------------------------------------------------|
| GET    | `/api/books/categories`          | Public     | List all book categories.                        |
| POST   | `/api/books/`                    | Admin      | Create a new book.                               |
| GET    | `/api/books/`                    | Public     | List/filter active books.                        |
| GET    | `/api/books/{book_id}`           | Public     | Get a book’s details.                            |
| PATCH  | `/api/books/{book_id}`           | Admin      | Update an existing book.                         |
| DELETE | `/api/books/{book_id}`           | Admin      | Soft-delete a book.                              |
| GET    | `/api/books/inactive`            | Admin      | List all soft-deleted books.                     |
| GET    | `/api/books/{book_id}/summary`   | Public     | Retrieve/generate AI-powered summary.            |
| POST   | `/api/books/{book_id}/reviews`   | Authenticated | Add a review.                                |
| GET    | `/api/books/{book_id}/reviews`   | Public     | List all reviews for a book.                     |

---

## 🛒 Orders Endpoints

| Method | Endpoint                             | Access        | Description                              |
|--------|--------------------------------------|---------------|------------------------------------------|
| GET    | `/api/orders/`                      | Authenticated | List orders for the current user.        |
| POST   | `/api/orders/`                      | Authenticated | Place a new order.                       |
| GET    | `/api/orders/{order_id}`           | Authenticated | Get details/status of an order.          |
| POST   | `/api/orders/{order_id}/cancel`    | Authenticated | Cancel a PENDING order.                  |
| POST   | `/api/orders/{order_id}/pay`       | Authenticated | Mark an order as "PAID".                 |
| PATCH  | `/api/orders/{order_id}/status`    | Admin         | Admin-only: force update order status.   |

---

# 🔄 Database Seeding

All seeding is handled by `seed_all.py` (called after migrations).

### ✅ Admin User

Creates a default admin user if none exists.

### 📚 Categories & Books

- Adds default categories if missing.
- For each book, generates a unique 13-digit ISBN.
- If a book with the same title exists, it’s skipped (idempotent).

### ▶️ When to Run

The entrypoint runs this at every startup:

```bash
flask db upgrade
python seed_all.py
```

It’s safe to run multiple times due to idempotency checks.

---

# ⚙️ WebSocket & Messaging

### `app/inventory/consumer.py`

- Connects to RabbitMQ (`order_created` queue).
- On each message:
  - Decrements stock.
  - Updates order status.
  - Emits WebSocket event to user room.

### `app/websocket/events.py`

- Defines `OrderNamespace`.
- Subscribes clients to rooms (named after their user ID).

### Front-end SPA (JS + HTML)

- Connects to Socket.IO at `http://<host>:5000`.
- Authenticates via JWT.
- Listens to real-time order updates.

---

# 🧪 Running Tests

```bash
# Optional: activate venv
source venv-bs/bin/activate

# Run tests with coverage
pytest --maxfail=1 --disable-warnings -q
```

Tests cover:

- **Auth**: registration, login, refresh, protection
- **Books**: CRUD, summaries, reviews
- **Orders**: place, cancel, pay, transitions
- **Consumer**: simulated RabbitMQ messages
- **WebSocket**: mocked Socket.IO events

---

# 🤝 Contributing

We welcome PRs, issues, or suggestions!

1. Fork the repository.
2. Create a topic branch: `git checkout -b feature/your-idea`.
3. Make changes (PEP8 + flake8 compliant).
4. Run tests.
5. Submit a Pull Request.

Please ensure new features are tested.

---

# 📄 License

MIT License. See `LICENSE` file for full details.

---

# 📘 Design Decisions & AI Integration

See [`DESIGN_DECISIONS.md`](./DESIGN_DECISIONS.md) for details on:

- Monolith vs Microservices
- Flask-Smorest, RabbitMQ, event queues
- OpenAI vs Cohere API
- Prompt design, caching
- WebSocket strategy & eventlet
- Debugging, extending the system
