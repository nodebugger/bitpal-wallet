"""Import all models here for Alembic to detect them."""
from app.db.session import Base

# Import models for Alembic to detect
from app.models.user import User  # noqa: F401
from app.models.wallet import Wallet  # noqa: F401
# from app.models.transaction import Transaction
# from app.models.api_key import APIKey
