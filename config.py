import os
from dotenv import load_dotenv

load_dotenv()  

TOKEN = os.getenv("TOKEN")
BASE = os.getenv("BASE")
UPLOAD_BASE = os.getenv("UPLOAD_BASE")

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "*/*",
}
