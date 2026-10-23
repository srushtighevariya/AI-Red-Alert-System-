from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Document Red Alert Detection System API"
    PROJECT_DESCRIPTION: str = (
        "Backend API for detecting risky, suspicious, and sensitive document content."
    )
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    MAX_UPLOAD_SIZE_MB: int = 10

    MONGODB_URL: str = "mongodb://localhost:27017/"
    MONGODB_DB_NAME: str = "red_alert_db"

    JWT_SECRET_KEY: str = "change_this_secret_key_later"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    OCR_LANGUAGES: str = "eng+guj"
    # Empty = find tesseract on PATH or in the default Windows install folder.
    TESSERACT_CMD: str = ""
    # Empty = use backend/tessdata (holds the Gujarati language file).
    TESSDATA_DIR: str = ""

    # AI model that reads meaning, not just keywords (needs torch + transformers).
    # The app works without it; the rule-based detectors still run.
    ENABLE_SEMANTIC_MODEL: bool = True
    SEMANTIC_MODEL_NAME: str = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"
    # How sure the model must be before a signal counts (0-1).
    SEMANTIC_THRESHOLD: float = 0.75

    FRONTEND_URL: str = "http://localhost:5173"

    API_V1_PREFIX: str = "/api/v1"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()