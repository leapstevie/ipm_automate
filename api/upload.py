import requests
from config import UPLOAD_BASE, TOKEN, HEADERS, BASE


def get_user_id():
    res = requests.get(f"{BASE}/users/me", headers=HEADERS)
    res.raise_for_status()
    return res.json()["data"]["id"]


def upload_temp_attachment(path_to_file):
    user_id = get_user_id()

    with open(path_to_file, "rb") as f:
        files = {"file": f}
        data = {"user_id": user_id}

        res = requests.post(
            f"{UPLOAD_BASE}/temp/upload/attachment",
            headers={"Authorization": f"Bearer {TOKEN}"},
            data=data,
            files=files,
        )

    res.raise_for_status()
    return res.json()["data"]["file_id"]


def upload_temp_image(path_to_image):
    user_id = get_user_id()

    with open(path_to_image, "rb") as f:
        files = {"file": f}
        data = {"user_id": user_id, "is_photo_id": "1"}

        res = requests.post(
            f"{UPLOAD_BASE}/temp/upload/image",
            headers={"Authorization": f"Bearer {TOKEN}"},
            data=data,
            files=files,
        )

    res.raise_for_status()
    return res.json()["data"]["file_id"]
