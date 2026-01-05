# steps/board_member.py

import random
import string
from api.upload import upload_temp_image
import os

def random_file(folder="picture_automate"):
    BASE_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(BASE_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")
    files = [f for f in os.listdir(abs_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate")
    return os.path.join(abs_folder, random.choice(files))

def random_note() -> str:
    return random.choice([
        "No additional remarks.",
        "All documents provided.",
        "Information is accurate to the best of our knowledge.",
        "Supporting documents attached.",
        "Reviewed and confirmed.",
    ])


def field_override(code):

    if code == "police_record_attachment_id":
        return upload_temp_image(random_file())
    
    if code == "board_member_note":
        return random_note()
    
    return None
