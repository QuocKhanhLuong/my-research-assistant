"""
Application configuration using Pydantic Settings.
Centralized configuration management with environment variable support.
"""
import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Info
    app_name: str = "Exam RAG API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # API Configuration
    api_v1_prefix: str = "/api/v1"
    
    # CORS Settings
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    # MegaLLM Configuration
    megallm_api_key: str = ""
    megallm_base_url: str = "https://ai.megallm.io/v1"
    llm_model: str = "llama3.3-70b-instruct"
    llm_temperature: float = 0.3
    
    # RAG Configuration
    pdf_directory: str = "./data/pdf"
    faiss_index_path: str = "./data/faiss_index"
    
    # Embedding Configuration
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    
    # Text Splitting Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Retrieval Configuration
    retrieval_k: int = 4
    
    def get_absolute_pdf_directory(self) -> str:
        """Get absolute path for PDF directory."""
        if os.path.isabs(self.pdf_directory):
            return self.pdf_directory
        # Relative to backend folder
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.normpath(os.path.join(backend_dir, self.pdf_directory))
    
    def get_absolute_index_path(self) -> str:
        """Get absolute path for FAISS index."""
        if os.path.isabs(self.faiss_index_path):
            return self.faiss_index_path
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.normpath(os.path.join(backend_dir, self.faiss_index_path))


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid re-reading env file on every call.
    """
    return Settings()


# Convenience export
settings = get_settings()
