import requests
import time
from config import STEP_NAME_QIP
from tokens import token_manager
from steps.generic_step import submit_generic_step
from steps.approval_flow import submit_signature, submit_payment, submit_invoice_paid
from steps.final_steps.preliminary_review import submit_flow


def wait_for_invoice_paid(
    invt_id: str,
    user_id: str | None = None,
    timeout_sec: int = 900,
    interval_sec: int = 30,
):
    start = time.time()
    last_info = None

    while True:
        try:
            info = submit_invoice_paid(invt_id, user_id=user_id)
            if info is not None:
                last_info = info
                status = (info or {}).get("status")
                paid_dt = (info or {}).get("paid_datetime")

                if status == "paid" and paid_dt:
                    # print(f"✔ Invoice paid at: {paid_dt}")
                    return info
        except Exception:
            pass

        if time.time() - start >= timeout_sec:
            # print("⚠️ Timeout waiting for invoice payment")
            return last_info

        time.sleep(interval_sec)


def run_all_steps(invt_id: str, user_id: str | None = None, return_config: dict | None = None):
    url = STEP_NAME_QIP
    res = requests.get(url, headers=token_manager.headers(user_id=user_id), timeout=360)
    res.raise_for_status()

    steps = sorted((res.json().get("data") or {}).get("qip") or [], key=lambda x: x.get("step_order", 0))

    print("\n========== START RUNNING ALL STEPS ==========")

    results = []
    for step in steps:
        code = step.get("code")
        if not code:
            continue

        print(f"\n🚀 Processing Step: {code}")
        try:
            ok = submit_generic_step(invt_id, code, user_id=user_id)   
            results.append({"code": code, "ok": bool(ok)})
        except Exception as e:
            print(f"[STEP] Error on '{code}': {e}")
            results.append({"code": code, "ok": False, "error": str(e)})

    try:
        submit_signature(invt_id, user_id=user_id)
        results.append({"code": "signature", "ok": True})
    except Exception as e:
        print(f"[SIGNATURE] Error: {e}")
        results.append({"code": "signature", "ok": False, "error": str(e)})

    try:
        submit_payment(invt_id, user_id=user_id)
        results.append({"code": "payment", "ok": True})
    except Exception as e:
        print(f"[PAYMENT] Error: {e}")
        results.append({"code": "payment", "ok": False, "error": str(e)})

    try:
        status_info = wait_for_invoice_paid(invt_id, user_id=user_id)
        results.append({"code": "invoice_status", "ok": True, "data": status_info})
    except Exception as e:
        print(f"[INVOICE] Error: {e}")
        results.append({"code": "invoice_status", "ok": False, "error": str(e)})

    try:
        submit_flow(invt_id, user_id=user_id, return_config=return_config)
        results.append({"code": "preliminary_review", "ok": True})
    except Exception as e:
        print(f"[PRELIM] Error: {e}")
        results.append({"code": "preliminary_review", "ok": False, "error": str(e)})

    print("\n========== ALL STEPS + SIGNATURE + PAYMENT COMPLETED ==========")
    return results
