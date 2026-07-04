import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    NOCODB_BASE_URL = os.getenv("NOCODB_BASE_URL", "").rstrip("/")
    NOCODB_TABLE_PATH = os.getenv("NOCODB_TABLE_PATH", "")
    NOCODB_TOKEN = os.getenv("NOCODB_TOKEN", "")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    JOB_DESCRIPTION = os.getenv("JOB_DESCRIPTION", "")

settings = Settings()