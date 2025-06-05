# 📖 Bookstore Backend

A robust RESTful API backend and real-time system for a bookstore. This backend handles authentication, book management, reviews, cart management, order processing and WebSocket-powered live notifications.

## 🌐 Features

* JWT-based Authentication (Login, Registration, Refresh, User Profile)
* Book Listings, Categories, and Reviews
* AI-Powered Book Summarisation (via Cohere API)
* Admin-only Book Management (CRUD)
* Cart System & Order Processing
* Order Status Enum (PENDING, PAID, SHIPPED, DELIVERED, CANCELLED, REFUNDED)
* Async Inventory Management (via RabbitMQ & Pika)
* Real-Time Order Notifications via WebSocket
* Login-enabled frontend SPA for real-time order subscription
* Flask-Smorest & Marshmallow for OpenAPI Docs

---

## 🧱 Setup Instructions

### ⚖️ Requirements

* Python 3.8+
* PostgreSQL
* RabbitMQ (AMQP)

### ⚡️ Installation

```bash
# Clone the project
$ git clone https://github.com/emmanueldev247/bookstore-backend.git
$ cd bookstore-backend

# Setup virtual environment
$ python3 -m venv venv-bs
$ source venv-bs/bin/activate

# Install dependencies
$ pip install -r requirements.txt

# Check RabbitMQ (should say connection succeeded)
$ nc -zv localhost 5672

# Setup PostgreSQL, Redis (follow .env or config.py for connection info)
```

---

## 💡 Project Structure

```plaintext
app/
├── auth/              # User registration, login, JWT token refresh, permissions
├── books/             # Book models, AI summary, category & review logic
├── orders/            # Order models, cart, order placing and tracking
├── inventory/         # Background consumer (RabbitMQ async queue)
├── websocket/         # Real-time events (Socket.IO)
├── static/            # CSS/JS for frontend SPA
├── templates/         # HTML templates
├── utils/             # Common utils, validators, blueprint registration
├── health/            # Health check routes
├── models/            # Base model declarations (e.g. User, Book)
├── config.py          # App settings/config
├── extensions.py      # Extensions: JWT, DB, Marshmallow, Celery, etc.
├── error_handlers.py  # Global error handling
```

---

## 🔒 Authentication API

| Method | Endpoint             | Access        | Description               |
| ------ | -------------------- | --------------| --------------------------|
| POST   | `/api/auth/register` | Public        | Register new user         |
| POST   | `/api/auth/login`    | Public        | Login user, return JWTs   |
| POST   | `/api/auth/refresh`  | Authenticated | Refresh access token      |
| GET    | `/api/auth/me`       | Authenticated | Get logged-in user's info |

---

## 📚 Books API

| Method | Endpoint                       | Access        | Description              |
| ------ | ------------------------------ | ------------- | ------------------------ |
| GET    | `/api/books/categories`        | Authenticated | List book categories     |
| POST   | `/api/books/`                  | Admin         | Add new book             |
| GET    | `/api/books/`                  | Authenticated | List/filter books        |
| GET    | `/api/books/{book_id}`         | Authenticated | View single book         |
| PATCH  | `/api/books/{book_id}`         | Admin         | Update book              |
| DELETE | `/api/books/{book_id}`         | Admin         | Soft delete              |
| GET    | `/api/books/inactive`          | Admin         | View soft-deleted books  |
| GET    | `/api/books/{book_id}/summary` | Authenticated | View/Generate AI summary |
| POST   | `/api/books/{book_id}/reviews` | Authenticated | Add review               |
| GET    | `/api/books/{book_id}/reviews` | Authenticated | View reviews             |

---

## 📦 Order API

| Method | Endpoint                        | Access        | Description            |
| ------ | ------------------------------- | ------------- | ---------------------- |
| GET    | `/api/orders/`                  | Authenticated | View all user orders   |
| POST   | `/api/orders/`                  | Authenticated | Place order using cart |
| GET    | `/api/orders/{order_id}`        | Authenticated | View specific order    |
| POST   | `/api/orders/{order_id}/cancel` | Authenticated | Cancel a PENDING order |
| POST   | `/api/orders/{order_id}/pay`    | Authenticated | View specific order    |
| PATCH  | `/api/orders/{order_id}/status` | Admin         | View specific order    |

### Order Flow

1. User adds books to cart (`CartItem` model).
2. User places order:

   * Cart items fetched
   * Books validated
   * `Order` and `OrderItems` created
   * Cart cleared
3. Order status starts as `PENDING`
4. Async inventory/notification tasks via RabbitMQ/SocketIO

---

## 🚚 Inventory (Async Queue)

* **app/inventory/consumer.py** listens for RabbitMQ events (e.g. stock management)
* Uses RabbitMQ (port 5672, tested via `nc`)

---

## 🛡️ WebSocket (WIP)

* **websocket/** contains support for real-time events
* Placeholder for future events like order updates, admin notifications, etc.

---

##  SPA – Single Page Application

* SPA frontend served from `/app/templates/`
   * `index.html`
* Static assets in `/app/static/`
   * `css/styles.css`
   * `js/app.js`
   * `js/socket.io.min.js`
* Authenticates using JWT
* Live order ID subscription & log stream
* Demo use: Connect, Subscribe, Watch Live Events

---

## 🎓 Technologies Used

* Flask + Flask-Smorest (REST API with OpenAPI)
* Flask-JWT-Extended (JWT authentication)
* Marshmallow (Serialization/Validation)
* Cohere API (Book summarisation)
* PostgreSQL (Relational DB)
* SQLAlchemy (ORM)
* RabbitMQ (Async processing)
* Docker & Docker Compose (WIP structure in `infra/`)
* Socket.IO + JavaScript (Frontend WebSocket SPA)
* HTML & CSS

---

## 🚧 To Do / Future Features

* [ ] Payment integration (Stripe/Paystack)
* [ ] Order status updates via admin panel
* [ ] Admin dashboard frontend
* [ ] Role-based access control improvements
* [ ] WebSocket real-time updates
* [ ] Unit tests and CI

---

## ✅ Contributing

Feel free to fork and raise PRs. Feedback and improvements welcome.

---

## 🚀 Quick Dev Commands

```bash
# Run migrations
flask db init
flask db migrate
flask db upgrade

# Run consumer (if implemented)
python -m app.inventory.consumer

# Check RabbitMQ running
nc -zv localhost 5672

# Run app
flask run
```

---

## 👤 Author

**Emmanuel Ademola** <br>
_Software Engineer_ <br>
[Portfolio](https://emmanueldev247.publicvm.com/) <br>
[GitHub: `@emmanueldev247`](https://github.com/emmanueldev247/)

---

## 📄 License

MIT
