# api/upload.py
import os
import requests
from config import UPLOAD_BASE, BASE
import tokens  


def get_user_id():
    url = f"{BASE}/users/me"
    res = requests.get(url, headers=tokens.token_manager.headers(), timeout=360)
    if res.status_code in (401, 403):
        try:
            tokens.token_manager.ensure_fresh()
            res = requests.get(url, headers=tokens.token_manager.headers(), timeout=360)
        except Exception:
            pass
    res.raise_for_status()
    return res.json()["data"]["id"]


def upload_temp_attachment(path_to_file):
    user_id = get_user_id()

    with open(path_to_file, "rb") as f:
        files = {"file": f}
        data = {"user_id": user_id}

        url = f"{UPLOAD_BASE}/temp/upload/attachment"
        res = requests.post(url, headers=tokens.token_manager.headers(), data=data, files=files, timeout=360)
        if res.status_code in (401, 403):
            try:
                tokens.token_manager.ensure_fresh()
                res = requests.post(url, headers=tokens.token_manager.headers(), data=data, files=files, timeout=360)
            except Exception:
                pass

    res.raise_for_status()
    return res.json()["data"]["file_id"]


def upload_temp_image(path_to_image):
    user_id = get_user_id()

    with open(path_to_image, "rb") as f:
        files = {"file": f}
        data = {"user_id": user_id, "is_photo_id": "1"}

        url = f"{UPLOAD_BASE}/temp/upload/image"
        res = requests.post(url, headers=tokens.token_manager.headers(), data=data, files=files, timeout=360)
        if res.status_code in (401, 403):
            try:
                tokens.token_manager.ensure_fresh()
                res = requests.post(url, headers=tokens.token_manager.headers(), data=data, files=files, timeout=360)
            except Exception:
                pass

    res.raise_for_status()
    return res.json()["data"]["file_id"]


def upload_list_excel(invt_id, list_code, xlsx_path):
    xlsx_path = os.path.abspath(xlsx_path)

    # print("[DEBUG] CWD =", os.getcwd())
    print("[DEBUG] Using Excel path =", xlsx_path)

    if not os.path.isfile(xlsx_path):
        raise FileNotFoundError(f"Excel not found: {xlsx_path}")

    url = f"{BASE}/invt/{invt_id}/list/{list_code}"

    with open(xlsx_path, "rb") as f:
        files = {
            "file": (
                os.path.basename(xlsx_path),
                f,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }

        res = requests.put(url, headers=tokens.token_manager.headers(), files=files, timeout=360)
        if res.status_code in (401, 403):
            try:
                tokens.token_manager.ensure_fresh()
                res = requests.put(url, headers=tokens.token_manager.headers(), files=files, timeout=360)
            except Exception:
                pass

    res.raise_for_status()
    return res.json()
