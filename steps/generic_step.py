from api.http import http_get, http_put
from utils.schema_payload import build_payload, _iter_fields
from utils.random_data import generic_value_resolver
from utils.applicant import ensure_primary_applicant


def build_auto_overrides(invt_id, detail):
    overrides = {}
    codes = []
    for f in _iter_fields(detail):
        code = f.get("code")
        if code:
            codes.append(code)

    target = []
    for c in codes:
        if "invt_applicant_people_information_id" in c:
            target.append(c)

    if target:
        applicant_id = ensure_primary_applicant(invt_id)
        for c in target:
            overrides[c] = applicant_id

    return overrides


def _process_subform(invt_id, subform, user_id=None):
    # print(f"[SUBFORM] Fetch meta for '{subform}'")
    meta = http_get(f"/invt/{invt_id}/subform/{subform}", user_id=user_id)["data"]
    objects = meta.get("objects") or []

    if objects:
        obj_id = objects[0]["id"]
    else:
        obj_id = meta.get("investment_info", {}).get("object_id")
        if not obj_id:
            raise Exception(f"Subform '{subform}' missing object_id")

    # print(f"[SUBFORM] Load data for object {obj_id}")
    data = http_get(
        f"/invt/{invt_id}/subform/{subform}",
        params={"object_id": obj_id},
        user_id=user_id,
    )["data"]

    detail = data.get("detail") or {}
    overrides = build_auto_overrides(invt_id, detail)
    payload = build_payload(detail, generic_value_resolver, overrides)

    # print(f"[SUBFORM] Save data for '{subform}' object {obj_id}")
    http_put(
        f"/invt/{invt_id}/subform/{subform}/object/{obj_id}/data/save?",
        {"data": payload},
        user_id=user_id,
    )


def _process_lists(invt_id, step_code, lists, user_id=None):
    if not lists:
        return False

    if step_code == "annex2_1":
        from steps.annex2_1 import upload_equipment_material_excel
        print("[STEP] Upload equipment/material Excel (annex2_1)")
        upload_equipment_material_excel(invt_id)  # if this does API calls, update it too
        return True

    if step_code == "annex2_2":
        from steps.annex2_2 import upload_product_input_excel
        print("[STEP] Upload product input Excel (annex2_2)")
        upload_product_input_excel(invt_id)  # if this does API calls, update it too
        return True

    for item in lists:
        subform = item.get("code")
        if not subform:
            continue

        count = 1 if step_code == "company_composition" else 1 #count many u want                    
        # print(f"[STEP] Process subform '{subform}' x{count}")

        for _ in range(count):
            _process_subform(invt_id, subform, user_id=user_id)

    return True


def submit_generic_step(invt_id, step_code, user_id: str | None = None):
    # print(f"[STEP] Begin '{step_code}' for {invt_id}")

    try:
        response = http_get(
            f"/step/{step_code}",
            params={"invt_id": invt_id, "type": "qip"},
            user_id=user_id,
        )
        data = response.get("data") or {}
        detail = data.get("detail") or {}
        # print(f"[STEP] Loaded detail for '{step_code}'")
    except Exception as e:
        print(f"[STEP] Failed to load detail for '{step_code}': {e}")
        detail = {}

    if not detail:
        # print(f"[STEP] No detail; processing subform '{step_code}'")
        _process_subform(invt_id, step_code, user_id=user_id)
        print(f"[STEP] Done '{step_code}'")
        return True

    forms = detail.get("forms") or []
    panels = detail.get("panels") or []
    lists = detail.get("lists") or []
    schema_code = detail.get("code")

    did_something = False

    if forms or panels:
        overrides = build_auto_overrides(invt_id, detail)
        payload = build_payload(detail, generic_value_resolver, overrides)
        # print(f"[STEP] Save forms/panels for '{step_code}'")
        http_put(
            f"/invt/{invt_id}/form/{step_code}/data/save?",
            {"data": payload},
            user_id=user_id,
        )
        did_something = True

    if lists:
        did_something = _process_lists(invt_id, step_code, lists, user_id=user_id)

    if not did_something and schema_code and schema_code != step_code:
        # print(f"[STEP] Fallback to schema code '{schema_code}'")
        _process_subform(invt_id, schema_code, user_id=user_id)
        print(f"[STEP] Done '{step_code}'")
        return True

    if not did_something:
        # print(f"[STEP] Final fallback; process '{step_code}'")
        _process_subform(invt_id, step_code, user_id=user_id)

    print(f"[STEP] Done '{step_code}'")
    return True
