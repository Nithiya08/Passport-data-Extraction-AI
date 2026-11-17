import os
from typing import List, Optional
from pydantic import Field
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings
    SettingsConfigDict = None


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    if SettingsConfigDict is not None:
        model_config = SettingsConfigDict(
            env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
            env_file_encoding="utf-8",
            extra="ignore"
        )

    GEMINI_API_KEY: str = Field(default="", description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-3.5-flash", description="Gemini model name")
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        description="Comma-separated CORS allowed origins"
    )
    PORT: int = Field(default=8000, description="Server port")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    MAX_FILES: Optional[int] = Field(default=None, description="Max files allowed per extraction request (None for unlimited)")
    MAX_FILE_SIZE_MB: Optional[int] = Field(default=None, description="Max file size in megabytes (None for unlimited)")
    MAX_IMAGE_DIMENSION: int = Field(default=2000, description="Max width/height for image resizing")
    PDF_DPI: int = Field(default=160, description="DPI for converting PDF pages to images (160 DPI is fast, sharp, and optimal for vision OCR)")
    ENABLE_FORENSIC_ENHANCEMENT: bool = Field(default=True, description="Enable forensic contrast stretching and sharpening for damaged/faded scans")

    @property
    def cors_origins(self) -> List[str]:
        """Parsed list of allowed CORS origins."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


settings = Settings()

