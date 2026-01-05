# steps/annex2_1.py
import os
from api.upload import upload_list_excel

LIST_CODE = "product_input"
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data_ipm", "cdcIPM-Sample-data"))
FILENAME = "1 - តារាងតម្រូវការធាតុចូលផលិតកម្ម.xlsx"

FOLDERS = (
    "តារាងតម្រូវការធាតុចូលផលិតកម្ម",
)


def find_equipment_excel_path(BASE_dir: str = BASE_DIR) -> str:

    for folder in FOLDERS:
        p = os.path.join(BASE_dir, folder, FILENAME)
        if os.path.isfile(p):
            return p

    for root, _, files in os.walk(BASE_dir):
        if FILENAME in files:
            return os.path.join(root, FILENAME)

    raise FileNotFoundError(f"Excel not found under: {BASE_dir}")


def upload_product_input_excel(invt_id, xlsx_path=None):
    xlsx_path = xlsx_path or find_equipment_excel_path()
    return upload_list_excel(invt_id=invt_id, list_code=LIST_CODE, xlsx_path=xlsx_path)


def field_override(code, context=None):
    if code != "product_input_excel_upload":
        return None

    invt_id = (context or {}).get("invt_id")
    if not invt_id:
        raise Exception("Missing invt_id in context")

    return upload_product_input_excel(invt_id)

