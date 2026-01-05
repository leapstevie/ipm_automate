import os
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from steps.general_info import field_override as general_override
from steps.company_composition import field_override as company_override
from steps.applicant_info import field_override as applicant_override
from steps.invt_info import field_override as invtinfo_override
from steps.board_member import field_override as boardmember_override
from steps.annex2_1 import field_override as annex2_1_override
from steps.investment_location import field_override as investmentlocation_override
from steps.product_and_labor import field_override as product_labor_override
from steps.utility_and_env import field_override as utility_env_override
from steps.annex2_2 import field_override as annex2_2_override

from api.http import http_get
from api.upload import upload_temp_attachment, upload_temp_image



_INVT_ENUM_CACHE: Optional[Dict[str, Any]] = None

# ENUM HELPERS

def _load_invt_enum() -> Dict[str, Any]:

    global _INVT_ENUM_CACHE
    if _INVT_ENUM_CACHE is None:
        res = http_get("/formdata/invt")
        _INVT_ENUM_CACHE = res.get("data", {}) or {}
    return _INVT_ENUM_CACHE


def _pick_from_option_code(option_code: Optional[str]) -> Optional[Any]:
    
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


def _pick_list_from_option_code(option_code: str, validation: Dict[str, Any]) -> List[Any]:
    
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


def _pick_dependent(keyword: Optional[str], parent_code: Optional[str]) -> Optional[Any]:

    if not keyword or not parent_code:
        return None

    try:
        res = http_get(
            "/formdata/invt/dependency_option",
            params={
                "keyword": keyword,
                "parent_code": parent_code,
            },
        )
        data = res.get("data") or []
        if not data:
            return None
        return random.choice(data).get("code")
    except Exception:
        return None


def _normalize_inline_options(options: List[Any]) -> List[Any]:

    values: List[Any] = []
    for o in options:
        v = o.get("value") if isinstance(o, dict) else o
        if v is not None:
            values.append(v)
    return values

# MAIN GENERIC RESOLVER

def generic_value_resolver(field: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Any:
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

    # 1) STEP-SPECIFIC OVERRIDES (invt_info first – dates, markets, etc.)

    v = invtinfo_override(code, context)
    if v is not None:
        return v

    v = general_override(code)
    if v is not None:
        return v

    v = company_override(code)
    if v is not None:
        return v

    v = applicant_override(code)
    if v is not None:
        return v

    v = boardmember_override(code)
    if v is not None:
        return v

    v = annex2_1_override(code)
    if v is not None:
        return v

    v = investmentlocation_override(code)
    if v is not None:
        return v

    v = product_labor_override(code)
    if v is not None:
        return v

    v = annex2_2_override(code, context)
    if v is not None:
        return v

    v = utility_env_override(code)
    if v is not None:
        return v


    # 2) READ-ONLY FIELDS – keep existing value

    if field.get("is_permanent_disable") and field.get("value") not in (None, ""):
        return field.get("value")

    # 3) FILE FIELDS
    if field_type == "attachment":
        from utils.random_data import random_file, random_face_file
        if "profile" in code_lower or "face" in code_lower:
            return upload_temp_attachment(random_face_file("picture_automate/face_scan"))
        return upload_temp_attachment(random_file("picture_automate"))

    if field_type == "image":
        from utils.random_data import random_file, random_face_file
        if "profile" in code_lower or "face" in code_lower:
            return upload_temp_image(random_face_file("picture_automate/face_scan"))
        return upload_temp_image(random_file("picture_automate"))

    # 4) DEPENDENCY FIELDS
    if dep_parent_key:
        parent_value = context.get(dep_parent_key)
        if parent_value:
            val = _pick_dependent(option_code, parent_value)
            if val:
                return val

    # 5) LIST FIELDS (data_type = list_of_string)
    if data_type == "list_of_string":

        if code == "investment_target_detail":
            enums = _load_invt_enum().get("investment_target", [])
            if not enums:
                return []

            group = next((g for g in enums if g.get("code") == "1"), None)
            if not group:
                return []

            children = group.get("children", [])
            child_codes = [c.get("code") for c in children if c.get("code")]
            if not child_codes:
                return []

            pick_count = min(3, len(child_codes))
            return random.sample(child_codes, pick_count)

        # Inline options on the field itself
        if options:
            list_values = _normalize_inline_options(options)
            if list_values:
                pick_count = min(3, len(list_values))
                return random.sample(list_values, pick_count)

        # Option enums
        if option_code:
            return _pick_list_from_option_code(option_code, validation)

        return []
    
    # ============================================================
    # 6) MULTI-SELECT
    # ============================================================
    if field_type == "multi_select":
        if option_code:
            return _pick_list_from_option_code(option_code, validation)
        if options:
            return [random.choice(options)]
        return []

    # ============================================================
    # 7) SINGLE SELECT FIELDS (select / radio / toggle)
    # ============================================================
    if option_code:
        picked = _pick_from_option_code(option_code)
        if picked is not None:
            return picked

    # ============================================================
    # 8) DATE FIELDS (non-timeline – timeline handled by invtinfo_override)
    # ============================================================
    if data_type == "date":
        from utils.random_data import random_past_date
        return random_past_date()

    # ============================================================
    # 9) LAT/LNG
    # ============================================================
    if "lat_lng" in code_lower:
        
        choices = [
            "11.808480,105.626298",
            "11.673732,105.378283",
            "13.375366,103.884511",
        ]
        
        return random.choice(choices)

    # ============================================================
    # 10) PASSPORT / ID
    # ============================================================
    if "passport" in code_lower or "citizen_id" in code_lower:
        from utils.random_data import random_passport
        return random_passport()

    # ============================================================
    # 11) INLINE OPTIONS (fallback)
    # ============================================================
    if options:
        inline_values = _normalize_inline_options(options)
        if inline_values:
            return random.choice(inline_values)

    # ============================================================
    # 12) EMAIL
    # ============================================================
    if "email" in code_lower:
        # Confirm email should match the first email
        if "confirm" in code_lower and "email" in context:
            return context["email"]

        from utils.random_data import random_email
        email = random_email()
        context["email"] = email
        return email

    # ============================================================
    # 13) PHONE
    # ============================================================
    if "phone" in code_lower and "code" not in code_lower:
        from utils.random_data import random_phone
        return random_phone()

    # ============================================================
    # 14) KHMER TEXT FIELDS
    # ============================================================
    if code_lower.endswith("_km") or code_lower.endswith("_kh"):
        from utils.random_data import random_company_name_km
        return random_company_name_km()

    # ============================================================
    # 15) ENGLISH TEXT FIELDS
    # ============================================================
    if code_lower.endswith("_en"):
        from utils.random_data import random_English_name
        return random_English_name()

    # ============================================================
    # 16) NUMERIC FIELDS
    # ============================================================
    numeric_types = {"int", "integer", "float", "decimal", "number"}
    if data_type in numeric_types:
        min_obj = validation.get("min")
        max_obj = validation.get("max")

        min_raw = min_obj.get("value") if isinstance(min_obj, dict) else min_obj
        max_raw = max_obj.get("value") if isinstance(max_obj, dict) else max_obj

        try:
            mn = float(min_raw) if min_raw not in (None, "") else 0.0
        except Exception:
            mn = 0.0

        try:
            mx = float(max_raw) if max_raw not in (None, "") else mn + 500.0
        except Exception:
            mx = mn + 500.0

        # If min > max, fix the range
        if mn > mx:
            mx = mn + 500.0

        if mx > 1000:
            mx = 1000

        if data_type == "float":
            return round(random.uniform(mn, mx), 2)

        return int(random.randint(int(mn), int(mx)))

    # ============================================================
    # 17) DEFAULT STRING
    # ============================================================
    return f"AUTO_{random.randint(1000, 9999)}"



# 5) PERSONAL INFO RANDOM
def random_foreign_commercial_company() -> str:
    options = [
        "foreign_commercial_company",
        "local_company",
        "joint_venture",
        "industrial_company",
        "service_company",
        "agriculture_company",
    ]
    return random.choice(options)


def random_English_name() -> str:
    return random.choice(["SomDara", "VongRith", "KimHeang", "SokLeap", "LongDara"])


def random_khmer_name() -> str:
    return random.choice(["ពីពពៃូឈ", "សុខ ដារ៉ា", "ជា ហេង", "ខឹម ហ៊ាង", "តេ តុលា", "រិត សុខា"])


def random_company_name_km() -> str:
    return random.choice([
        "គៅគៃ", "លីម៉េង", "សេងហួរ", "តាយ៉ុង", "អាយអិនជីនៀរ", "អេសជីអិល", "អេសអេសអេស",
        "អេសអេចខេ", "អាយអាយអាយ", "អេសធីអាយ", "អេសជីធី", "អេអាយធី", "អេធីឃេ",
    ])


def random_passport() -> str:
    return "A" + "".join(random.choices(string.digits, k=9))


def random_email() -> str:
    return f"{''.join(random.choices(string.ascii_lowercase, k=8))}@mailinator.com"


def random_phone() -> str:
    prefixes = ["012", "015", "017", "010", "087", "089", "098", "099", "071"]
    return random.choice(prefixes) + "".join(random.choices(string.digits, k=6))


def random_address() -> str:
    return random.choice(["Street 123", "Street 456", "Street 78A", "ផ្លូវ៣៣៤", "ផ្លូវ៤៥៦", "ផ្លូវ២១៣"])


def random_past_date(max_days: int = 2000) -> str:
    dt = datetime.now() - timedelta(days=random.randint(1, max_days))
    return dt.strftime("%Y-%m-%d")


# ======================================================
# 6) FILE HELPERS
# ======================================================

def random_file(folder: str = "picture_automate") -> str:
    BASE_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(BASE_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")
    files = [f for f in os.listdir(abs_folder)
             if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate/")
    return os.path.join(abs_folder, random.choice(files))


def random_signature_file(folder: str = "picture_automate/signature") -> str:
    BASE_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(BASE_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")
    files = [f for f in os.listdir(abs_folder)
             if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate/signature")
    return os.path.join(abs_folder, random.choice(files))


def random_face_file(folder: str = "picture_automate/face_scan") -> str:
    BASE_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    abs_folder = os.path.abspath(os.path.join(BASE_dir, folder))
    if not os.path.isdir(abs_folder):
        raise Exception(f"Folder not found: {abs_folder}")
    files = [f for f in os.listdir(abs_folder)
             if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not files:
        raise Exception("No images found in picture_automate/face_scan")
    return os.path.join(abs_folder, random.choice(files))
