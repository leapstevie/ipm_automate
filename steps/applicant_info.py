import random
import string
from datetime import datetime, timedelta
from api.upload import upload_temp_attachment, upload_temp_image
import os


def random_face_file(folder="picture_automate/face_scan"):
    BASE_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(BASE_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")
    files = [f for f in os.listdir(abs_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate/face_scan")
    return os.path.join(abs_folder, random.choice(files))


def random_file(folder="picture_automate"):
    BASE_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(BASE_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")
    files = [f for f in os.listdir(abs_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate/")
    return os.path.join(abs_folder, random.choice(files))

def random_fullname():
    first = random.choice([
        "Sok", "Dara", "Vichea", "Sreymom", "Sreyleak",
        "Rith", "Kosal", "Malis", "Chenda", "Vanda"
    ])
    last = random.choice([
        "Chan", "Kim", "Leng", "Heng", "Long", "Sao", "Sok", "Rin", "Vong"
    ])
    return f"{first} {last}"


def random_passport_number():
    return "A" + "".join(random.choices(string.digits, k=9))


def random_issue_date():
    dt = datetime.now() - timedelta(days=random.randint(90, 1800))
    return dt.strftime("%Y-%m-%d")


def random_phone_number():
    return "".join(random.choices(string.digits, k=9))


def random_email():
    name = "".join(random.choices(string.ascii_lowercase, k=8))
    domain = "".join(random.choices(string.ascii_lowercase, k=5))
    return f"{name}@{domain}.com"


def random_address():
    return random.choice([
        "Phnom Penh, Cambodia",
        "Kandal Province",
        "Takeo Province",
        "Battambang City",
        "Siem Reap City",
        "STREET 1234",
    ])


# ======================================================
# FIELD-LEVEL OVERRIDE LOGIC
# ======================================================

def field_override(code):

    if code == "profile_photo_id":
        return upload_temp_image(random_face_file())

    if code == "citizen_id_or_passport_attachment_id":
        return upload_temp_attachment(random_file())

    if code == "fullname":
        return random_fullname()

    if code == "citizen_id_or_passport_number":
        return random_passport_number()

    if code == "citizen_id_or_passport_issued_datetime":
        return random_issue_date()

    if code == "phone_number":
        return random_phone_number()

    if code == "email":
        return random_email()

    if code == "address":
        return random_address()

    return None
