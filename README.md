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
# Apply all migrations
alembic upgrade head

# Verify tables created
alembic current
```

### 5. Run the Application

```bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000

# With specific settings
uvicorn app.main:app --host localhost --port 8000 --workers 1
```

### 6. Verify Installation

```bash
# Check database connection
python -c "from app.db.session import engine; print('✅ Database connected')"

# Visit in browser or via curl:
http://localhost:8000/            # API root
http://localhost:8000/health      # Health check
http://localhost:8000/docs        # Interactive API documentation
http://localhost:8000/redoc       # Alternative API documentation
```

## Project Structure

```
bitpal-wallet/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py           # Google OAuth endpoints
│   │   │   ├── keys.py           # API key management
│   │   │   ├── wallet.py         # Wallet operations
│   │   │   └── general.py        # Health checks
│   │   ├── api_router.py         # Route aggregation
│   │   └── dependencies.py       # Auth dependencies
│   ├── core/
│   │   └── config.py             # Settings & configuration
│   ├── db/
│   │   └── session.py            # Database engine & session
│   ├── models/
│   │   ├── user.py               # User model
│   │   ├── wallet.py             # Wallet model
│   │   ├── api_key.py            # API key model
│   │   └── transaction.py        # Transaction model
│   ├── schemas/                  # Pydantic request/response schemas
│   ├── services/
│   │   ├── auth_service.py       # Google OAuth logic
│   │   ├── api_key_service.py    # API key business logic
│   │   ├── wallet_service.py     # Wallet operations
│   │   └── paystack_service.py   # Paystack integration
│   └── main.py                   # FastAPI app with lifespan
├── alembic/
│   ├── versions/                 # Database migrations
│   └── env.py                    # Alembic configuration
├── docker-compose.yml            # PostgreSQL container
├── Dockerfile                    # Application container
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── alembic.ini                   # Alembic config
├── API_DOCUMENTATION.md          # Complete API reference
└── README.md                     # This file
```

## API Endpoints

### Authentication (`/auth`)
- `GET /auth/google` - Initiate Google OAuth sign-in (returns URL or redirects)
- `GET /auth/google/callback` - OAuth callback handler

### API Key Management (`/keys`)
- `POST /keys/create` - Generate new API key with permissions
- `GET /keys/list` - List all keys (shows active, expired, revoked status)
- `POST /keys/rollover` - Create new key from expired key's permissions
- `DELETE /keys/{key_id}` - Revoke API key

### Wallet Operations (`/wallet`)
- `POST /wallet/deposit` - Initiate Paystack deposit
- `POST /wallet/paystack/webhook` - Paystack webhook endpoint (called by Paystack)
- `GET /wallet/balance` - Get current wallet balance
- `GET /wallet/transactions` - Get transaction history
- `GET /wallet/deposit/{reference}/status` - Check deposit status
- `POST /wallet/transfer` - Transfer funds to another wallet

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete endpoint specifications.

```

## Database Migrations

### Create new migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Description of changes"

# Or create empty migration
alembic revision -m "Migration name"
```

### Apply migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific number of migrations
alembic upgrade +2

# Rollback migrations
alembic downgrade -1

# Check current version
alembic current
```

## Development

### Code Style

```bash
# Format code
black app/

# Check imports
pylint app/

# Type checking (if using mypy)
mypy app/
```

### Database

The project uses PostgreSQL with async SQLAlchemy (2.0.45+). All database operations are async-safe.

**Key features:**
- Async engine with asyncpg driver
- pgbouncer compatibility (prepared statement cache disabled)
- Automatic migration management with Alembic
- Soft deletes on API keys (revoked flag)

## Key Features Explained

### Dual Authentication

**JWT (Google OAuth)**
- User signs in via Google
- Server returns JWT token
- Token valid for 24 hours
- Required for OAuth-initiated actions

**API Keys**
- User-generated service credentials
- Permission-based (deposit, transfer, read)
- Expirable (1H, 1D, 1M, 1Y)
- Revokable at any time
- Maximum 5 active keys per user
- Automatically marked inactive when expired

### Payment Processing

**Paystack Integration**
- User initiates deposit with amount
- Server returns Paystack checkout URL
- User completes payment on Paystack
- Paystack sends HMAC-signed webhook
- Webhook credits user's wallet
- Idempotent webhook handling (no duplicate credits)

### Transfers

- Atomic transactions (sender and receiver updated together)
- Balance validation before transfer
- Transaction history for both parties
- Works with JWT or API keys (with transfer permission)

### API Key Expiry

- Keys automatically marked inactive when expired
- Two-stage marking:
  1. **Lazy marking** - When expired key used for authentication
  2. **Proactive marking** - When listing user's keys
- Expired keys still count toward 5-key limit (can be revoked to free slot)
- Rollover feature to create new key from expired key's permissions

## Troubleshooting

### Database Connection Failed

```bash
# Verify DATABASE_URL in .env
# Format: postgresql+asyncpg://user:password@host:port/database

# Test connection
python -c "from app.db.session import engine; import asyncio; asyncio.run(engine.connect())"
```

### OAuth Redirect Error

- Ensure `GOOGLE_CLIENT_ID` is set
- Verify callback URL: `http://localhost:8000/api/v1/auth/google/callback`
- Add to Google Console allowed redirect URIs

### Paystack Webhook Not Working

- Use ngrok to expose local server: `ngrok http 8000`
- Set webhook URL in Paystack dashboard: `{ngrok_url}/api/v1/wallet/paystack/webhook`
- Verify `PAYSTACK_SECRET_KEY` is correct

## License

MIT
