import requests
from api.http import http_get     
from api.upload import upload_temp_attachment
from utils.random_data import random_signature_file
from config import BASE, TOKEN     


def submit_signature(invt_id):
    http_get(f"/invt/{invt_id}/confirmation")
    
    signature_path = random_signature_file()
    signature_file_id = upload_temp_attachment(signature_path)

    with open(signature_path, "rb") as f:
        files = {"file": f}

        res = requests.put(
            f"{BASE}/invt/{invt_id}/application/sign?",
            headers={"Authorization": f"Bearer {TOKEN}"},  
            files=files,
        )

    print("==================== SIGN DEBUG ====================")
    print("URL:", res.request.url)
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)
    print("===================================================")

    res.raise_for_status()

    print("✔ Signature completed for:", invt_id)
    return True
