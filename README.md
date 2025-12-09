# Bitpal Wallet Service

A production-ready wallet service with Paystack integration, JWT authentication, and API key management.

## Features

- 🔐 Dual Authentication (JWT + API Keys)
- 💰 Paystack Payment Integration
- 💸 Wallet-to-Wallet Transfers
- 📊 Transaction History
- 🔑 Permission-Based API Keys
- 🔄 Idempotent Webhook Handling

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL with asyncpg
- **ORM:** SQLAlchemy 2.0 (async)
- **Authentication:** Google OAuth 2.0, JWT
- **Payment:** Paystack

## Quick Start

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Google OAuth credentials
- Paystack account

### 2. Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# - DATABASE_URL
# - GOOGLE_CLIENT_ID & SECRET
# - PAYSTACK_SECRET_KEY
# - SECRET_KEY (generate with: openssl rand -hex 32)
```

### 4. Database Setup

```bash
# Initialize Alembic (if not done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 5. Run the Application

```bash
# Development mode
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. Verify Installation

Visit:
- API Root: http://localhost:8000/
- Health Check: http://localhost:8000/health
- API Docs: http://localhost:8000/docs

## Project Structure

```
bitpal-wallet/
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Configuration
│   ├── db/           # Database setup
│   ├── models/       # SQLAlchemy models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   └── main.py       # FastAPI app
├── alembic/          # Database migrations
├── tests/            # Test suite
├── .env.example      # Environment template
├── requirements.txt  # Dependencies
└── README.md
```

## API Endpoints

### Authentication
- `POST /auth/google` - Google OAuth login

### API Keys
- `POST /keys/create` - Generate API key
- `POST /keys/rollover` - Rollover expired key

### Wallet Operations
- `POST /wallet/deposit` - Initiate deposit
- `POST /wallet/paystack/webhook` - Paystack webhook
- `GET /wallet/balance` - Get balance
- `POST /wallet/transfer` - Transfer funds
- `GET /wallet/transactions` - Transaction history

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black app/

# Lint
pylint app/
```

## License

MIT
