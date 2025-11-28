import os
import random
import string
from datetime import datetime, timedelta
from api.http import http_get
from api.upload import upload_temp_attachment, upload_temp_image

_INVT_ENUM_CACHE = None


def _load_invt_enum():
    global _INVT_ENUM_CACHE
    if _INVT_ENUM_CACHE is None:
        res = http_get("/formdata/invt")
        _INVT_ENUM_CACHE = res.get("data", {})
    return _INVT_ENUM_CACHE


def _pick_from_option_code(option_code: str):
    if not option_code:
        return None

    enums = _load_invt_enum()
    items = enums.get(option_code) or []
    if not items:
        return None

    codes = [item.get("code") for item in items if item.get("code")]
    if codes:
        return random.choice(codes)

    values = [item.get("value") for item in items if item.get("value") is not None]
    if values:
        return random.choice(values)

    return None


def _pick_list_from_option_code(option_code: str, validation: dict):
    enums = _load_invt_enum().get(option_code, [])
    codes = [i.get("code") for i in enums if i.get("code")]
    if not codes:
        return []


    min_len = 1
    try:
        block = validation.get("min_length")
        val = block.get("value") if isinstance(block, dict) else block
        if val not in (None, ""):
            min_len = int(val)
    except Exception:
        pass

    max_pick = min(3, len(codes))  
    pick_count = min(max(1, min_len), max_pick)

    return random.sample(codes, pick_count)


def _pick_dependent(keyword, parent_code):
    try:
        res = http_get(
            "/formdata/invt/dependency_option",
            params={"keyword": keyword, "parent_code": parent_code},
        )
        data = res.get("data", [])
        if not data:
            print(f"[WARN] No dependent options for {keyword} parent={parent_code}")
            return None
        return random.choice(data).get("code")

    except Exception as e:
        print(f"[ERROR] Dependency-option failed for keyword={keyword} parent={parent_code}: {e}")
        return None


def generic_value_resolver(field, context=None):
    if context is None:
        context = {}

    code = (field.get("code") or "").strip()
    code_lower = code.lower()
    validation = field.get("validation") or {}
    data_type_raw = validation.get("data_type")
    data_type = (data_type_raw.get("value") if isinstance(data_type_raw, dict) else data_type_raw or "").lower()

    field_type = (field.get("field_type_code") or "").lower()
    option_code = field.get("option_code")
    dep_parent_key = field.get("dependency_option_field_code")
    options = field.get("value_list") or []

    # ============================================================
    # READ-ONLY FIELDS
    # ============================================================
    if field.get("is_permanent_disable") and field.get("value") not in (None, ""):
        return field.get("value")

    # ============================================================
    # FILE FIELDS
    # ============================================================
    if field_type == "attachment":
        from utils.random_data import random_file
        return upload_temp_attachment(random_file("picture_automate/face_scan"))

    if field_type == "image":
        from utils.random_data import random_file
        return upload_temp_image(random_file("picture_automate"))

    # ============================================================
    # DEPENDENCY FIELDS
    # ============================================================
    if dep_parent_key:
        parent_value = context.get(dep_parent_key)
        if parent_value:
            val = _pick_dependent(option_code, parent_value)
            if val:
                return val

    # ============================================================
    # LIST FIELDS (data_type = list_of_string)
    # ============================================================
    if data_type == "list_of_string":

        # SPECIAL RULE FOR investment_target_detail
        if code == "investment_target_detail":

            enums = _load_invt_enum().get("investment_target", [])
            if not enums:
                return []

            # ---- ALWAYS SELECT GROUP 1 ----
            group = next((g for g in enums if g.get("code") == "1"), None)
            if not group:
                return []

            # ---- ONLY CHILDREN FROM GROUP 1 ----
            children = group.get("children", [])
            child_codes = [c.get("code") for c in children if c.get("code")]

            if not child_codes:
                return []

            # ---- Pick 1–3 children randomly ----
            pick_count = min(3, len(child_codes))
            return random.sample(child_codes, pick_count)

        # ------------------------------------------------------------
        # NORMAL CASE: inline value_list
        # ------------------------------------------------------------
        if options:
            list_values = []
            for o in options:
                if isinstance(o, dict):
                    v = o.get("value")
                else:
                    v = o
                if v is not None:
                    list_values.append(v)

            if list_values:
                pick_count = min(3, len(list_values))
                return random.sample(list_values, pick_count)

        # ------------------------------------------------------------
        # OPTION ENUMS
        # ------------------------------------------------------------
        if option_code:
            return _pick_list_from_option_code(option_code, validation)

        return []


    # ============================================================
    # MULTI-SELECT
    # ============================================================
    if field_type == "multi_select":
        if option_code:
            return _pick_list_from_option_code(option_code, validation)
        if options:
            return [random.choice(options)]
        return []

    # ============================================================
    # SINGLE SELECT FIELDS
    # ============================================================
    if option_code:
        picked = _pick_from_option_code(option_code)
        if picked is not None:
            return picked

    # ============================================================
    # DATE FIELDS
    # ============================================================
    if data_type == "date":
        from utils.random_data import random_past_date
        return random_past_date()

    # ============================================================
    # LAT/LNG
    # ============================================================
    if "lat_lng" in code_lower:
        lat = round(random.uniform(10.0, 14.5), 6)
        lng = round(random.uniform(102.0, 107.0), 6)
        return f"{lat},{lng}"

    # ============================================================
    # PASSPORT / ID
    # ============================================================
    if "passport" in code_lower or "citizen_id" in code_lower:
        from utils.random_data import random_passport
        return random_passport()

    # ============================================================
    # INLINE OPTIONS (fallback)
    # ============================================================
    if options:
        inline_values = []
        for o in options:
            if isinstance(o, dict):
                v = o.get("value")
            else:
                v = o
            if v is not None:
                inline_values.append(v)

        if inline_values:
            return random.choice(inline_values)

    # ============================================================
    # EMAIL
    # ============================================================
    if "email" in code_lower:
        if "confirm" in code_lower and "email" in context:
            return context["email"]

        from utils.random_data import random_email
        email = random_email()
        context["email"] = email
        return email

    # ============================================================
    # PHONE
    # ============================================================
    if "phone" in code_lower and "code" not in code_lower:
        from utils.random_data import random_phone
        return random_phone()

    # ============================================================
    # KHMER TEXT FIELDS
    # ============================================================
    if code_lower.endswith("_km") or code_lower.endswith("_kh"):
        from utils.random_data import random_company_name_km
        return random_company_name_km()

    # ============================================================
    # ENGLISH TEXT FIELDS
    # ============================================================
    if code_lower.endswith("_en"):
        from utils.random_data import random_English_name
        return random_English_name()

    # ============================================================
    # NUMERIC FIELDS
    # ============================================================
    numeric_types = {"int", "integer", "float", "decimal", "number"}
    if data_type in numeric_types:
        min_obj = validation.get("min")
        max_obj = validation.get("max")

        min_raw = min_obj.get("value") if isinstance(min_obj, dict) else min_obj
        max_raw = max_obj.get("value") if isinstance(max_obj, dict) else max_obj

        try:
            mn = float(min_raw) if min_raw not in (None, "") else 0
        except:
            mn = 0

        try:
            mx = float(max_raw) if max_raw not in (None, "") else mn + 500
        except:
            mx = mn + 500

        if mn > mx:
            mx = mn + 500

        if mx > 1_000_00:
            mx = 1_000_00

        if data_type == "float":
            return round(random.uniform(mn, mx))

        return int(random.randint(int(mn), int(mx)))

    # ============================================================
    # DEFAULT STRING
    # ============================================================
    return f"AUTO_{random.randint(1000, 9999)}"


# ======================================================
# 5) PERSONAL INFO RANDOM
# ======================================================

def random_foreign_commercial_company():
    options = [
        "foreign_commercial_company",
        "local_company",
        "joint_venture",
        "industrial_company",
        "service_company",
        "agriculture_company",
    ]
    return random.choice(options)

def random_English_name():
    return random.choice(["SomDara", "VongRith", "KimHeang", "SokLeap", "LongDara"])

def random_khmer_name():
    return random.choice(["ពីពពៃូឈ", "សុខ ដារ៉ា", "ជា ហេង", "ខឹម ហ៊ាង", "តេ តុលា", "រិត សុខា"])

def random_company_name_km():
    return random.choice([
        "គៅគៃ", "លីម៉េង", "សេងហួរ", "តាយ៉ុង", "អាយអិនជីនៀរ", "អេសជីអិល", "អេសអេសអេស",
        "អេសអេចខេ", "អាយអាយអាយ", "អេសធីអាយ", "អេសជីធី", "អេអាយធី", "អេធីឃេ",
    ])

def random_passport():
    return "A" + "".join(random.choices(string.digits, k=9))

def random_email():
    return f"{''.join(random.choices(string.ascii_lowercase, k=8))}@mailinator.com"

def random_phone():
    return "8" + "".join(random.choices(string.digits, k=10))

def random_address():
    return random.choice(["Street 123", "Street 456", "Street 78A", "ផ្លូវ៣៣៤", "ផ្លូវ៤៥៦", "ផ្លូវ២១៣"])

def random_past_date(max_days=2000):
    dt = datetime.now() - timedelta(days=random.randint(1, max_days))
    return dt.strftime("%Y-%m-%d")


# ======================================================
# 6) FILE HELPERS
# ======================================================

def random_file(folder="picture_automate"):
    if not os.path.isdir(folder):
        raise Exception(f"Folder not found: {folder}")
    files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate/")
    return os.path.join(folder, random.choice(files))

def random_signature_file(folder="picture_automate/signature"):
    if not os.path.isdir(folder):
        raise Exception(f"Folder not found: {folder}")
    files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate/signature")
    return os.path.join(folder, random.choice(files))

def random_face_file(folder="picture_automate/face_scan"):
    if not os.path.isdir(folder):
        raise Exception(f"Folder not found: {folder}")
    files = [f for f in os.listdir(folder) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate/face_scan")
    return os.path.join(folder, random.choice(files))

# ======================================================
# 7) EQUIPMENT RANDOM
# ======================================================

def random_equipment_name():
    return random.choice([
        "Steel Rod", "Welding Helmet", "Cement Bag", "Steel Pipe",
        "Safety Shoes", "Electric Drill", "Hammer",
        "Aluminum Sheet", "Air Compressor", "Cutting Blade", "Industrial Fan",
    ])
# ======================================================
# 8) PROJECT INFO RANDOM
# ======================================================

def random_building_type():
    return random.choice(["existing_building", "new_building"])

def random_cost(min_v=1000, max_v=100000):
    return str(random.randint(min_v, max_v))

def random_area():
    return str(random.randint(100, 20000))

def random_capital_percent():
    own = random.randint(10, 80)
    long_term = random.randint(0, 50)
    short_term = random.randint(0, 100 - own)
    return str(own), str(long_term), str(short_term)

def random_project_dates():
    start = datetime.now() + timedelta(days=random.randint(30, 120))
    end   = start + timedelta(days=random.randint(30, 120))
    equip = end   + timedelta(days=random.randint(30, 120))
    prod  = equip + timedelta(days=random.randint(30, 120))
    return (
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d"),
        equip.strftime("%Y-%m-%d"),
        prod.strftime("%Y-%m-%d")
    )


# ======================================================
# 9) SMALL UTILITIES
# ======================================================


def random_future_date():
    dt = datetime.now() + timedelta(days=random.randint(30, 500))
    return dt.strftime("%Y-%m-%d")

def random_product_name():
    return random.choice(["ផលិតផល A", "ផលិតផល B", "ផលិតផល C", "ទំនិញ X", "ទំនិញ Y"])

def random_hs_code():
    return "".join(random.choices(string.digits, k=6))

def random_kh_note():
    return random.choice(["ល្អ", "ធម្មតា", "គុណភាពខ្ពស់", "ត្រូវការកែប្រែ", "សាកល្បង"])

def random_labor_type():
    return random.choice([
        "management", "engineers", "technician", "supervisors",
        "office_staff", "unskilled_worker", "monitor", "worker",
        "nurse", "pharmacy_staff", "administrative_staff", "other",
    ])

def random_kh_text():
    return random.choice(["ល្អ", "សាកល្បង", "ពិភាក្សា", "គម្រោង", "បរិស្ថាន"])

def random_product_input_name():
    return random.choice(["ស្រូវ", "កៅស៊ូ", "ស្ករ", "សំបុក", "ជ័រ", "ខ្សែ", "ដែក", "សន្លឹកដែក"])
