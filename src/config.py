"""Configuration module for the NovaMart Assistant project.

Reads environment variables using Python's standard library to keep the
setup clean, modular, and safe.
"""

import os

APP_NAME = os.getenv("APP_NAME", "novamart-assistant")
APP_ENV = os.getenv("APP_ENV", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# OpenAI AI Provider Configuration
# The API key must always be read from the environment and NEVER hardcoded.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
