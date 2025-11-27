# steps/generic_step.py

from api.http import http_get, http_put
from utils.schema_payload import build_payload
from utils.random_data import generic_value_resolver


# ==================================================================
# 1) Process a SUBFORM (universal handler)
# ==================================================================
def _process_subform(invt_id, subform: str) -> bool:
    print(f"[SUBFORM] Loading subform: {subform}")

    # Load row list
    sf = http_get(f"/invt/{invt_id}/subform/{subform}")["data"]
    objects = sf.get("objects") or []

    # Determine object_id
    if objects:
        obj_id = objects[0]["id"]
    else:
        obj_id = sf.get("investment_info", {}).get("object_id")
        if not obj_id:
            raise Exception(f"[ERROR] Subform '{subform}' missing object_id")

        # Backend requires an empty row before saving
        http_put(
            f"/invt/{invt_id}/subform/{subform}/data/save?",
            {"data": [{}]},
        )

    print(f"[SUBFORM] Using object_id = {obj_id}")

    # Load schema for that row
    popup = http_get(
        f"/invt/{invt_id}/subform/{subform}",
        params={"object_id": obj_id},
    )["data"]

    detail = popup.get("detail") or {}

    # Build dynamic payload
    payload = build_payload(detail, generic_value_resolver)

    # Save final data
    http_put(
        f"/invt/{invt_id}/subform/{subform}/object/{obj_id}/data/save?",
        {"data": payload},
    )

    print(f"[OK] SUBFORM {subform} saved.\n")
    return True


# ==================================================================
# 2) MAIN STEP HANDLER — UNIVERSAL (wrapper, form, subform)
# ==================================================================
def submit_generic_step(invt_id, step_code: str) -> bool:
    print(f"\n[GENERIC] Submitting step: {step_code}")

    detail = None
    try:
        response = http_get(
            f"/step/{step_code}",
            params={"invt_id": invt_id, "type": "qip"},
        )
        step_data = response.get("data") or {}
        detail = step_data.get("detail") or {}
    except Exception:
        # /step/{step_code} might not exist → handled below as subform
        pass

    if detail is not None:
        forms = detail.get("forms") or []
        lists = detail.get("lists") or []

        # WRAPPER → contains subforms
        if not forms and lists:
            print(f"[GENERIC] Wrapper detected: {step_code}")
            for item in lists:
                subform = item["code"]
                print(f"[GENERIC] → Processing subform: {subform}")
                _process_subform(invt_id, subform)
            print(f"[GENERIC] Finished wrapper: {step_code}\n")
            return True

        # NORMAL FORM STEP
        if forms or detail.get("panels"):
            print(f"[GENERIC] FORM step: {step_code}")

            payload = build_payload(detail, generic_value_resolver)

            http_put(
                f"/invt/{invt_id}/form/{step_code}/data/save?",
                {"data": payload},
            )

            print(f"[GENERIC] {step_code} saved (FORM)\n")
            return True

    # FALLBACK → treat step_code as subform directly
    print(f"[GENERIC] Fallback → treating '{step_code}' as subform")
    _process_subform(invt_id, step_code)
    print(f"[GENERIC] {step_code} saved (SUBFORM fallback)\n")
    return True
