
import random
import string
from api.upload import upload_temp_attachment, upload_temp_image
import os


# ======================================================
# REAL FILE PICKER FOR ATTACHMENTS
# ======================================================

def random_file(folder="picture_automate"):

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(base_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")
    files = [
        f for f in os.listdir(abs_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    if not files:
        raise Exception("No images found in picture_automate/")
    return os.path.join(abs_folder, random.choice(files))

def random_face_file(folder="picture_automate/face_scan"):
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(base_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")
    files = [f for f in os.listdir(abs_folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate/face_scan")
    return os.path.join(abs_folder, random.choice(files))

# ======================================================
# REALISTIC COMPANY PARENT NAMES
# ======================================================

def random_company_parent_name():
    return random.choice([
        "Global Holdings Corporation",
        "Sunrise International Group Ltd.",
        "Eastern Manufacturing Corporation",
        "Silver River Global Industries",
        "Prime Asia Investment Holdings",
        "United Global Trading & Development",
        "Evergreen Industrial Group",
        "NorthStar International Ventures",
        "BlueStone Capital Partners",
        "Asia-Pacific Industrial Alliance",
    ])


# ======================================================
# ADDRESSES (clean corporate-style)
# ======================================================

def random_address():
    return random.choice([
        "No. 45, Preah Norodom Blvd, Phnom Penh, Cambodia",
        "15th Floor, Central World Tower, Bangkok, Thailand",
        "District 1, Ho Chi Minh City, Vietnam",
        "Gangnam-daero, Seoul, South Korea",
        "Raffles Place, Singapore",
        "Street 215, Toul Kork, Phnom Penh, Cambodia",
    ])


# ======================================================
# WEBSITE & EMAIL (realistic corporate format)
# ======================================================

def random_corp_domain():
    name = "".join(random.choices(string.ascii_lowercase, k=8))
    tld = random.choice([".com", ".co", ".biz", ".corp"])
    return f"{name}{tld}"


def random_website():

    return f"www.{random_corp_domain()}"


def random_email():
    # e.g. james@oceangroup.com
    username = "".join(random.choices(string.ascii_lowercase, k=6))
    domain = random_corp_domain()
    return f"{username}@{domain}"

def random_note():
    return random.choice([
        "Primary shareholder",  
        "Valid registration provided",
        "Corporate records verified",
        "Supporting documents attached",
        "AUTO-generated shareholder entry",
    ])



def field_override(code):
    if code == "share_holder_company_parent_registration_number":
        return random.choice([
            "1234567890",
            "9876543210",
            "5555555555",
            "4444444444",
            "3333333333",
        ])
    
    if code == "share_holder_police_record_attachment_id":
        return upload_temp_attachment(random_file())

    if code == "legal_representative_certificate_attachment_id":
        return upload_temp_image(random_face_file())



    if code == "share_holder_attachment_id":
        return upload_temp_attachment(random_file())

    if code == "share_holder_company_registration_attachment_id":
        return upload_temp_attachment(random_file())

    if code == "share_holder_company_parent_record_attachment_id":
        return upload_temp_attachment(random_file())

    if code == "share_holder_note":
        return random_note()

    # -----------------------------------
    # COMPANY PARENT INFO
    # -----------------------------------
    if code == "share_holder_company_parent_name":
        return random_company_parent_name()

    if code == "share_holder_company_parent_address":
        return random_address()

    if code == "share_holder_company_parent_email":
        return random_email()

    if code == "share_holder_company_parent_website":
        return random_website()

    return None
