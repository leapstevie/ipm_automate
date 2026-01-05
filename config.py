import os
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DOTENV_PATH = os.path.join(PROJECT_ROOT, ".env")
load_dotenv(DOTENV_PATH)


QIP_BASE_URL = (os.getenv("QIP_BASE_URL") or "").strip().rstrip("/")
UPLOAD_BASE = (os.getenv("UPLOAD_BASE") or "").strip().rstrip("/")
STEP_NAME_QIP = (os.getenv("STEP_NAME_QIP") or "").strip()

if not QIP_BASE_URL or not UPLOAD_BASE:
    raise RuntimeError("Missing required env: QIP_BASE_URL/UPLOAD_BASE")

DMB_DIRECT_PAYMENT_ENDPOINT = (os.getenv("DMB_DIRECT_PAYMENT_ENDPOINT") or "").strip()
DMB_DIRECT_PAYMENT_TOKEN = (os.getenv("DMB_DIRECT_PAYMENT_TOKEN") or "").strip()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT"))
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_QIP_NAME = os.getenv("DB_QIP_NAME")

DEFAULT_PASSWORD = (os.getenv("DEFAULT_PASSWORD") or "").strip()

