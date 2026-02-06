"""
Configuration - Environment-based configuration for the application.
"""

import os
from pathlib import Path

# Get the project root directory (where spec-driven-development folder is)
_PROJECT_ROOT = Path(__file__).parent.parent.resolve()


def _resolve_path(env_var: str, default_relative: str) -> Path:
    """Resolve a path from environment or default, ensuring it's absolute."""
    env_value = os.environ.get(env_var)
    if env_value:
        path = Path(env_value)
        return path.resolve() if not path.is_absolute() else path
    return (_PROJECT_ROOT / default_relative).resolve()


class Config:
    """Application configuration"""

    # Database - always use absolute path
    DATABASE_PATH = _resolve_path("DATABASE_PATH", "data/app.db")

    # Generated tests output - always use absolute path
    GENERATED_TESTS_DIR = _resolve_path("GENERATED_TESTS_DIR", "generated_tests")

    # Default target URL for running tests
    DEFAULT_TARGET_URL = os.environ.get("DEFAULT_TARGET_URL", "http://localhost:8001")

    # LLM configuration
    # Supported providers: "mock", "openai", "anthropic"
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "mock")

    # API Keys (set the one for your chosen provider)
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

    # Legacy support: LLM_API_KEY works as fallback
    LLM_API_KEY = os.environ.get("LLM_API_KEY")

    # Model configuration
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")

    # Check if real LLM is configured
    @property
    def USE_REAL_LLM(self) -> bool:
        if self.LLM_PROVIDER == "mock":
            return False
        if self.LLM_PROVIDER == "openai":
            return bool(self.OPENAI_API_KEY or self.LLM_API_KEY)
        if self.LLM_PROVIDER == "anthropic":
            return bool(self.ANTHROPIC_API_KEY or self.LLM_API_KEY)
        return False

    # Test execution
    TEST_TIMEOUT = int(os.environ.get("TEST_TIMEOUT", "300"))


config = Config()
