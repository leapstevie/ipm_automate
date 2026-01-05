import os
import mimetypes
import requests

from api.http import http_get
from tokens import token_manager
from utils.random_data import random_signature_file
from config import BASE , DMB_DIRECT_PAYMENT_ENDPOINT, DMB_DIRECT_PAYMENT_TOKEN


def submit_signature(invt_id: str, user_id: str | None = None):

    try:
        http_get(f"/invt/{invt_id}/confirmation", user_id=user_id)
    except Exception as e:
        print(f"[SIGNATURE] Confirmation check failed, proceeding anyway: {e}")

    signature_path = random_signature_file()

    filename = os.path.basename(signature_path)
    ext = os.path.splitext(filename)[1].lower()
    if ext in (".jpg", ".jpeg"):
        mime_type = "image/jpeg"
    elif ext == ".png":
        mime_type = "image/png"
    else:
        mime_type = mimetypes.guess_type(signature_path)[0] or "image/jpeg"

    url = f"{BASE.rstrip('/')}/invt/{invt_id}/application/sign"

    with open(signature_path, "rb") as f:
        files = {"file": (filename, f, mime_type)}

        # 1st try
        res = requests.put(url, headers=token_manager.headers(user_id=user_id), files=files, timeout=360)

        if res.status_code in (401, 403):
            token_manager.on_unauthorized(user_id=user_id)
            res = requests.put(url, headers=token_manager.headers(user_id=user_id), files=files, timeout=360)

    # print("==================== SIGN DEBUG ====================")
    # print("URL:", getattr(res.request, "url", url))
    # print("FILENAME:", filename)
    # print("MIME:", mime_type)
    # print("STATUS:", res.status_code)
    # print("RESPONSE:", res.text)
    # print("===================================================")

    res.raise_for_status()
    print(f"✔ Signature completed ")
    return True


def submit_payment(invt_id: str, user_id: str | None = None):
    resp = http_get(f"/invt/{invt_id}/confirmation", user_id=user_id)

    data = resp.get("data") or {}
    invoice = data.get("invoice") or {}
    ref = invoice.get("osp_invoice_code")

    if not DMB_DIRECT_PAYMENT_ENDPOINT or not DMB_DIRECT_PAYMENT_TOKEN:
        raise RuntimeError("Missing DMB_DIRECT_PAYMENT_ENDPOINT or DMB_DIRECT_PAYMENT_TOKEN env")

    if not ref:
        raise RuntimeError("Missing osp_invoice_code from confirmation")

    ref = str(ref).strip() 
    
    url = f"{DMB_DIRECT_PAYMENT_ENDPOINT}?reference_number={ref}"

    print("==================== DMB PAY DEBUG ====================")
    print("URL:", url)
    print("REFERENCE:", ref)

    res = requests.post(
        url,
        headers={"Authorization": f"Bearer {DMB_DIRECT_PAYMENT_TOKEN}"},
        timeout=(10, 600),   
    )

    # print("STATUS:", res.status_code)
    # print("RESPONSE:", res.text)
    # print("======================================================")

    res.raise_for_status()
    # Force single line output explicitly
    print(f"✔ Payment requested for reference_number: {ref}", flush=True)
    return True


def submit_invoice_paid(invt_id: str, user_id: str | None = None):
    resp = http_get(f"/invt/{invt_id}/confirmation", user_id=user_id)

    data = resp.get("data") or {}
    invoice = data.get("invoice") or {}
    status = (invoice.get("invoice_status") or {}).get("keyword")
    paid_dt = invoice.get("paid_datetime")

    # print("==================== INVOICE STATUS ====================")
    # print("STATUS:", status)
    # print("PAID_DATETIME:", paid_dt)
    # print("========================================================")

    print(f"✔ Invoice status: {status}")

    return {
        "status": status,
        "paid_datetime": paid_dt,
        "invoice_code": invoice.get("osp_invoice_code"),
    }
