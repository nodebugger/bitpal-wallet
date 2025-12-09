from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    # Database
    DATABASE_URL: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    
    # Paystack
    PAYSTACK_SECRET_KEY: str
    PAYSTACK_PUBLIC_KEY: str
    
    # Application
    APP_NAME: str = "Bitpal Wallet Service"
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()