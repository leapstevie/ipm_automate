# steps/generic_step.py

from api.http import http_get, http_put
from utils.schema_payload import build_payload, _iter_fields
from utils.random_data import generic_value_resolver
from utils.applicant import ensure_primary_applicant


def build_auto_overrides(invt_id, detail):

    overrides = {}

    fields = list(_iter_fields(detail))
    codes = [f.get("code") for f in fields if f.get("code")]

    if any("invt_applicant_people_information_id" in c for c in codes):
        applicant_id = ensure_primary_applicant(invt_id)
        for code in codes:
            if "invt_applicant_people_information_id" in code:
                overrides[code] = applicant_id

    return overrides


# -------------------------------------------------------
# PROCESS A SINGLE SUBFORM (share_holder, board_member, etc.)
# -------------------------------------------------------
def _process_subform(invt_id, subform):
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

        # reload to get created row
        sf = http_get(f"/invt/{invt_id}/subform/{subform}")["data"]
        objects = sf.get("objects") or []
        if objects:
            obj_id = objects[0]["id"]

    print(f"[SUBFORM] Using object_id = {obj_id}")

    # Load schema for this object
    popup = http_get(
        f"/invt/{invt_id}/subform/{subform}",
        params={"object_id": obj_id},
    )["data"]

    detail = popup.get("detail") or {}

    # Apply auto overrides for this subform
    overrides = build_auto_overrides(invt_id, detail)

    # Build dynamic payload
    payload = build_payload(detail, generic_value_resolver, overrides)

    # Save final data
    http_put(
        f"/invt/{invt_id}/subform/{subform}/object/{obj_id}/data/save?",
        {"data": payload},
    )

    print(f"[OK] SUBFORM {subform} saved.\n")
    return True


# -------------------------------------------------------
# MAIN STEP HANDLER (GENERIC FOR ALL STEPS)
# -------------------------------------------------------
def submit_generic_step(invt_id, step_code):
    print(f"\n[GENERIC] Submitting step: {step_code}")

    # 1) Try to load /step/{step_code}
    try:
        response = http_get(
            f"/step/{step_code}",
            params={"invt_id": invt_id, "type": "qip"},
        )
        step_data = response.get("data") or {}
        detail = step_data.get("detail") or {}
    except Exception as e:
        print(f"[GENERIC] Warning: cannot load /step/{step_code}: {e}")
        detail = {}

    # 2) If no detail at all → treat as a pure subform
    if not detail:
        print(f"[GENERIC] No detail → treating '{step_code}' as subform")
        _process_subform(invt_id, step_code)
        print(f"[GENERIC] {step_code} saved (SUBFORM fallback)\n")
        return True

    forms = detail.get("forms") or []
    panels = detail.get("panels") or []
    lists = detail.get("lists") or []
    schema_code = detail.get("code")

    did_something = False

    # ---------------------------------------------------
    # A) FORM PART (top-level fields)
    #    - company_composition uses this (share percentages)
    #    - applicant, invt_info, etc. also use this
    # ---------------------------------------------------
    if forms or panels:
        print(f"[GENERIC] FORM part detected for step: {step_code}")

        overrides = build_auto_overrides(invt_id, detail)
        payload = build_payload(detail, generic_value_resolver, overrides)

        http_put(
            f"/invt/{invt_id}/form/{step_code}/data/save?",
            {"data": payload},
        )

        print(f"[GENERIC] {step_code} saved (FORM)")
        did_something = True

    # ---------------------------------------------------
    # B) LISTS PART (wrapper of subforms)
    #    - company_composition.lists includes "share_holder"
    #    - board_member_composition has "board_member" in lists
    # ---------------------------------------------------
    if lists:
        print(f"[GENERIC] Wrapper (lists) detected for step: {step_code}")
        for item in lists:
            subform = item["code"]
            print(f"[GENERIC] → Processing subform from lists: {subform}")
            _process_subform(invt_id, subform)
        print(f"[GENERIC] Finished wrapper lists for: {step_code}")
        did_something = True

    # ---------------------------------------------------
    # C) SUBFORM-STYLE STEP (no forms/lists, but different schema code)
    # ---------------------------------------------------
    if (not did_something) and schema_code and schema_code != step_code:
        print(
            f"[GENERIC] Subform-style step detected: "
            f"step_code={step_code}, schema_code={schema_code}"
        )
        _process_subform(invt_id, schema_code)
        print(f"[GENERIC] {step_code} saved via subform '{schema_code}'\n")
        return True

    # ---------------------------------------------------
    # D) Fallback (if nothing above matched)
    # ---------------------------------------------------
    if not did_something:
        print(f"[GENERIC] Final fallback → treating '{step_code}' as subform")
        _process_subform(invt_id, step_code)
        print(f"[GENERIC] {step_code} saved (SUBFORM fallback)\n")

    return True
