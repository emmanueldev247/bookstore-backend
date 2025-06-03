# 📖 Bookstore Backend

A fully-featured RESTful API backend for a bookstore. This backend handles user authentication, book listings, reviews, order processing, cart management, and real-time events.

## 🌐 Features

* JWT-based Authentication (Login, Registration, Refresh, User Profile)
* Book Listings and Reviews
* Category Management
* Admin-only Book Management (CRUD)
* Cart System
* Order Processing and Tracking
* Order Status Enum (Pending, Paid, Shipped, Cancelled, Refunded)
* RabbitMQ Integration for Async Task Queue (via Inventory App)
* AI-Powered Book Summarisation (via Cohere API)
* WebSocket Event System Setup for Realtime Integrations
* Flask-Smorest + Marshmallow for OpenAPI documentation

---

## 🧱 Setup Instructions

### ⚖️ Requirements

* Python 3.8+
* PostgreSQL
* Redis
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
├── inventory/         # Background consumer (Celery-based)
├── websocket/         # Placeholder for real-time events
├── utils/             # Common utils, validators, blueprint registration
├── health/            # Health check routes
├── models/            # Base model declarations (e.g. User, Book)
├── config.py          # App settings/config
├── extensions.py      # Extensions: JWT, DB, Marshmallow, Celery, etc.
├── error_handlers.py  # Global error handling
```

---

## 🔒 Authentication API

| Method | Endpoint             | Description               |
| ------ | -------------------- | ------------------------- |
| POST   | `/api/auth/register` | Register new user         |
| POST   | `/api/auth/login`    | Login user, return JWTs   |
| POST   | `/api/auth/refresh`  | Refresh access token      |
| GET    | `/api/auth/me`       | Get logged-in user's info |

---

## 📚 Books API

| Method | Endpoint                       | Access        | Description              |
| ------ | ------------------------------ | ------------- | ------------------------ |
| GET    | `/api/books/categories`        | Public        | List book categories     |
| POST   | `/api/books/`                  | Admin         | Add new book             |
| GET    | `/api/books/`                  | Public        | List/filter books        |
| GET    | `/api/books/{book_id}`         | Public        | View single book         |
| PATCH  | `/api/books/{book_id}`         | Admin         | Update book              |
| DELETE | `/api/books/{book_id}`         | Admin         | Soft delete              |
| GET    | `/api/books/inactive`          | Admin         | View soft-deleted books  |
| GET    | `/api/books/{book_id}/summary` | Public        | View/Generate AI summary |
| POST   | `/api/books/{book_id}/reviews` | Authenticated | Add review               |
| GET    | `/api/books/{book_id}/reviews` | Public        | View reviews             |

---

## 📦 Order API

| Method | Endpoint                 | Access        | Description            |
| ------ | ------------------------ | ------------- | ---------------------- |
| POST   | `/api/orders/`           | Authenticated | Place order using cart |
| GET    | `/api/orders/`           | Authenticated | View all user orders   |
| GET    | `/api/orders/{order_id}` | Authenticated | View specific order    |

### Order Flow

1. User adds books to cart (`CartItem` model).
2. User places order:

   * Cart items fetched
   * Books validated
   * `Order` and `OrderItems` created
   * Cart cleared
3. Order status starts as `PENDING`
4. Future enhancements may include webhook updates (e.g. payment success -> `PAID`)

---

## 🚚 Inventory (Async Queue)

* **inventory/consumer.py** listens for events (e.g. stock management, email notifications)
* Uses RabbitMQ (port 5672, tested via `nc`)
* Can be extended with Celery tasks

---

## 🛡️ WebSocket (WIP)

* **websocket/** contains initial support for real-time events
* Placeholder for future events like order updates, admin notifications, etc.

---

## 🎓 Technologies Used

* Flask + Flask-Smorest (Blueprint-based REST API with OpenAPI)
* SQLAlchemy (ORM)
* Marshmallow (Serialization/Validation)
* PostgreSQL (Relational DB)
* RabbitMQ (Async processing)
* Cohere API (Book summarisation)
* Flask-JWT-Extended (JWT authentication)

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
# Run app
flask run

# Run migrations
flask db init
flask db migrate
flask db upgrade

# Check RabbitMQ running
nc -zv localhost 5672

# Run consumer (if implemented)
celery -A app.inventory.consumer worker --loglevel=info
```

---

## 👤 Author

**Emmanuel Ademola**
Backend Developer | MEDIA10 STUDIOS
[Portfolio](https://emmanueldev247.publicvm.com/)
GitHub: `@emmanueldev247`

---

## 📄 License

MIT - Use it freely, credit is appreciated.
