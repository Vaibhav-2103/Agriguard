import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PORT: int = 10000
    DATABASE_URL: str = "sqlite:///./data/agriguard.db"
    JWT_SECRET: str = "supersecretagriguardkey2026changethisinprod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    MODEL_PATH: str = "ml/outputs/agriguard_model.onnx"
    CLASS_NAMES_PATH: str = "ml/outputs/class_names.json"
    KNOWLEDGE_BASE_PATH: str = "knowledge/diseases.json"
    CHATBOT_BACKEND: str = "rules"  # "rules" or "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    UPLOAD_DIR: str = "uploads"
    ALLOWED_ORIGINS: str = "*"
    SEED_DEMO: bool = False
    
    # Image resize max dimension (memory optimization)
    MAX_IMAGE_DIM: int = 1024
    
    # Heuristics & Confidence thresholds
    CONFIDENCE_REJECT_THRESHOLD: float = 0.60
    CONFIDENCE_CERTAINTY_THRESHOLD: float = 0.85
    SEVERITY_LOW_THRESHOLD: float = 0.10
    SEVERITY_MEDIUM_THRESHOLD: float = 0.30

    # Image validation thresholds
    MIN_IMAGE_DIM: int = 64
    MAX_FILE_SIZE_BYTES: int = 8 * 1024 * 1024  # 8 MB
    BLUR_LAPLACIAN_VAR_THRESHOLD: float = 40.0
    BRIGHTNESS_MIN: float = 30.0
    BRIGHTNESS_MAX: float = 230.0
    MIN_LEAF_COLOR_PERCENT: float = 5.0  # At least 5% green/vegetative color

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

# Validate JWT_SECRET in production / Render
is_prod = os.getenv("RENDER") or os.getenv("NODE_ENV") == "production"
if is_prod:
    if not settings.JWT_SECRET or settings.JWT_SECRET == "supersecretagriguardkey2026changethisinprod":
        raise ValueError(
            "CRITICAL SECURITY ERROR: In production, you MUST provide a unique, secure JWT_SECRET environment variable."
        )

# Ensure database directory exists if sqlite
if "sqlite" in settings.DATABASE_URL:
    db_file_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if "/" in db_file_path or "\\" in db_file_path:
        db_dir = Path(db_file_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path("data").mkdir(parents=True, exist_ok=True)
