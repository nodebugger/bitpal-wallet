# Phase 1 Setup Instructions

## What We've Built

Phase 1 of the Bitpal Wallet Service is now complete! Here's what has been set up:

✅ Project structure with modular architecture
✅ FastAPI application with health check endpoint
✅ Async SQLAlchemy database configuration
✅ Alembic migrations setup
✅ Environment configuration using Pydantic Settings
✅ Requirements file with all dependencies

## Next Steps to Get Running

### 1. Create Virtual Environment & Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL Database

```bash
# Using PostgreSQL CLI
createdb bitpal_wallet

# Or using psql
psql -U postgres
CREATE DATABASE bitpal_wallet;
\q
```

### 3. Configure Environment Variables

```bash
# Copy the template
cp .env.example .env

# Edit .env with your actual values
```

**Required changes in `.env`:**
- `DATABASE_URL`: Update with your PostgreSQL credentials
- `SECRET_KEY`: Generate with `openssl rand -hex 32` or Python:
  ```python
  import secrets
  print(secrets.token_hex(32))
  ```
- Google OAuth credentials (can use placeholders for now)
- Paystack keys (can use placeholders for now)

### 4. Test the Setup

```bash
# Run the application
uvicorn app.main:app --reload

# In another terminal, test the endpoints:
# Root endpoint
curl http://localhost:8000/

# Health check (tests DB connection)
curl http://localhost:8000/health
```

### 5. Access API Documentation

Open your browser to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Expected Responses

### Root Endpoint (`GET /`)
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Bitpal Wallet Service API",
  "data": {
    "version": "1.0.0",
    "docs": "/docs"
  }
}
```

### Health Check (`GET /health`)
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Service is healthy",
  "data": {
    "api": "operational",
    "database": "connected"
  }
}
```

## Troubleshooting

### Database Connection Error
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL in `.env`
- Ensure database exists: `psql -l`

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### Port Already in Use
- Change port: `uvicorn app.main:app --reload --port 8001`
- Or kill process using port 8000

## What's Next?

Phase 1 is complete! You're now ready for **Phase 2: Authentication & User Management**.

In Phase 2, we'll implement:
- User and Wallet models
- Google OAuth integration
- JWT token generation
- Protected endpoints

To proceed to Phase 2, confirm:
- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] PostgreSQL running
- [ ] `.env` file configured
- [ ] Health check returns "database: connected"
