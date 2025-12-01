# steps/generic_step.py

from api.http import http_get, http_put
from utils.schema_payload import build_payload, _iter_fields
from utils.random_data import generic_value_resolver
from utils.applicant import ensure_primary_applicant


# -------------------------------------------------------
# AUTO-OVERRIDES BUILDER
# -------------------------------------------------------
def build_auto_overrides(invt_id, detail):
    overrides = {}
    fields = list(_iter_fields(detail))
    codes = [f.get("code") for f in fields if f.get("code")]

    if any("invt_applicant_people_information_id" in c for c in codes):
        applicant_id = ensure_primary_applicant(invt_id)
        for c in codes:
            if "invt_applicant_people_information_id" in c:
                overrides[c] = applicant_id

    return overrides


# -------------------------------------------------------
# PROCESS A SINGLE SUBFORM
# -------------------------------------------------------
def _process_subform(invt_id, subform):
    sf = http_get(f"/invt/{invt_id}/subform/{subform}")["data"]
    objects = sf.get("objects") or []

    if objects:
        obj_id = objects[0]["id"]
    else:
        obj_id = sf.get("investment_info", {}).get("object_id")
        if not obj_id:
            raise Exception(f"Subform '{subform}' missing object_id")

    popup = http_get(
        f"/invt/{invt_id}/subform/{subform}",
        params={"object_id": obj_id},
    )["data"]

    detail = popup.get("detail") or {}
    overrides = build_auto_overrides(invt_id, detail)
    payload = build_payload(detail, generic_value_resolver, overrides)

    http_put(
        f"/invt/{invt_id}/subform/{subform}/object/{obj_id}/data/save?",
        {"data": payload},
    )

    return True


# -------------------------------------------------------
# MAIN GENERIC STEP HANDLER
# -------------------------------------------------------
def submit_generic_step(invt_id, step_code):
    try:
        response = http_get(
            f"/step/{step_code}",
            params={"invt_id": invt_id, "type": "qip"},
        )
        step_data = response.get("data") or {}
        detail = step_data.get("detail") or {}
    except Exception:
        detail = {}

    if not detail:
        _process_subform(invt_id, step_code)
        return True

    forms = detail.get("forms") or []
    panels = detail.get("panels") or []
    lists = detail.get("lists") or []
    schema_code = detail.get("code")

    did_something = False

    if forms or panels:
        overrides = build_auto_overrides(invt_id, detail)
        payload = build_payload(detail, generic_value_resolver, overrides)
        http_put(
            f"/invt/{invt_id}/form/{step_code}/data/save?",
            {"data": payload},
        )
        did_something = True

    if lists:
        for item in lists:
            subform = item["code"]
            _process_subform(invt_id, subform)
        did_something = True

    if not did_something and schema_code and schema_code != step_code:
        _process_subform(invt_id, schema_code)
        return True

    if not did_something:
        _process_subform(invt_id, step_code)

    return True
