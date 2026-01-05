# steps/general_info.py

import random
import string
import os
from api.upload import upload_temp_attachment, upload_temp_image
# ======================================================
# COMPANY NAME PAIRS

_COMPANY_NAME_PAIRS = [
    ("សេង ហួរ", "SENG HOUR"),
    ("លី ម៉េង", "LI MENG"),
    ("អេ អាយ ភី អិល តិចណូឡូជី", "AIPL TECHNOLOGY"),
    ("អាន់គ័រ គន្សត្រាក់សិន", "ANGKOR CONSTRUCTION"),
    ("វត្តននា អ៊ិនដាស្ត្រី", "VATTANANA INDUSTRY"),
    ("រតនៈ អភិវឌ្ឍន៍", "RATTANA DEVELOPMENT"),
    ("សុភមង្គល ឧស្សាហកម្ម", "SOPHEAKMONGKOL INDUSTRIAL"),
    ("មេគង្គ ត្រេតឌីង", "MEKONG TRADING"),
    ("ហេង លី អ៊ិនជីនៀរីង", "HENG LY ENGINEERING"),
    ("ភ្នំពេញ ឌីជីថល សឺវីស", "PHNOM PENH DIGITAL SERVICES"),
]

def random_file(folder="picture_automate"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(base_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")
    files = [f for f in os.listdir(abs_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate")
    return os.path.join(abs_folder, random.choice(files))



def random_company_pair():
    km, en = random.choice(_COMPANY_NAME_PAIRS)
    return f"ក្រុមហ៊ុន {km}", f"{en.upper()} CO., LTD."


def random_phone():
    prefixes = ["012", "015", "017", "010", "087", "089", "098", "099", "071"]
    return random.choice(prefixes) + "".join(random.choices(string.digits, k=6))


# ======================================================
# STREET NAMES``
# ======================================================

def random_street_name_km():
    return random.choice([
        "ផ្លូវ ១២០", "ផ្លូវ ២៧១", "ផ្លូវ ១៩៨៦",
        "ផ្លូវ ៣៣០", "ផ្លូវ ៥១៧", "ផ្លូវ ៧មករា",
        "ផ្លូវ ទួលគោក", "ផ្លូវ ស្ទឹងមានជ័យ", "ផ្លូវ ៣៥១",
    ])


def random_street_name_en():
    return random.choice([
        "Street 271", "Street 1986", "Monivong Blvd",
        "Russian Blvd", "Sihanouk Blvd", "Norodom Blvd",
        "Central Market Road", "Diamond Island Road",
    ])


# ======================================================
# NUMERIC FIELDS
# ======================================================

def random_land_number():
    return str(random.randint(100, 9999))


def random_building_number():
    return f"B{random.randint(1, 99)}"


def random_house_number():
    return str(random.randint(1, 999))


def random_large_number():
    return random.randint(100_000, 999_999)


def random_very_large_number():
    return random.randint(5_000_000, 50_000_000)


# ======================================================
# INDUSTRIAL PARKS
# ======================================================

def random_industrial_park_name():
    return random.choice([
        "PPSEZ (Phnom Penh SEZ)",
        "Manhattan SEZ",
        "VSIP Industrial Park",
        "Sihanoukville SEZ",
        "Cambodia-Japan SEZ",
        "Royal Group SEZ",
        "Vattanac Industrial Park",
    ])


# ======================================================
# LOCATION DESCRIPTION
# ======================================================

def random_location_description_km():
    return random.choice([
        "ជិតផ្សារទួលសង្កែ",
        "ក្បែរ​មហាវិថី​មុនីវង្ស",
        "ជាប់ផ្លូវធំ",
        "នៅក្បែររោងចក្រ",
        "ជិតសាលារៀន",
        "ក្រោយផ្សារចាស់",
    ])


def random_location_description_en():
    return random.choice([
        "Near main road",
        "Close to industrial zone",
        "Next to factory area",
        "Near school zone",
        "Behind market",
        "Beside warehouse",
    ])


# ======================================================
# FIELD-LEVEL OVERRIDE LOGIC (Hook for generic_value_resolver)
# ======================================================

def field_override(code):


    # -------------------
    # CUSTOM COMPANY NAME
    # -------------------
    if code == "company_name_km":
        km, _ = random_company_pair()
        return km

    if code == "company_name_en":
        _, en = random_company_pair()
        return en
    
    if code == "company_name_reservation_attachment_id":
       return upload_temp_image(random_file())

    if code == "contact_phone_number":
        return random_phone()

    if code == "contact_street_no":
        return random_street_name_km()

    if code == "contact_street_no_en":
        return random_street_name_en()

    if code == "contact_land_number":
        return random_land_number()

    if code == "contact_building_number":
        return random_building_number()

    if code == "contact_house_number":
        return random_house_number()

    if code == "contact_industrial_park":
        return random_industrial_park_name()

    if code == "contact_industrial_park_en":
        return random_industrial_park_name()

    if code == "contact_location_description":
        return random_location_description_km()

    if code == "contact_location_description_en":
        return random_location_description_en()

    if code == "company_info_register_capital_value":
        return random_very_large_number()

    if code == "company_info_total_share":
        return random_large_number()

    if code == "company_info_value_per_share_value":
        return random_large_number()

    return None
