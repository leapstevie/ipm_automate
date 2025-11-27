from api.http import http_get, http_put
from utils.random_data import generic_value_resolver
from utils.schema_payload import build_payload


def debug_print_field_codes(detail):
    print("=== APPLICANT FIELD CODES FROM SERVER ===")
    for form in detail.get("forms", []):
        for panel in form.get("panels", []):
            for group in panel.get("field_groups", []):
                for field in group.get("fields", []):
                    print(" ->", field.get("code"))
    print("========================================")


def resolve_applicant_value(field, ctx=None):
    return generic_value_resolver(field, ctx or {})


def submit_applicant_step(invt_id, applicant_id):

    print(f"[APPLICANT] Using applicant_id = {applicant_id}")

    res = http_get("/step/applicant", params={"invt_id": invt_id, "type": "qip"})
    detail = res["data"]["detail"]

    overrides = {
        "invt_applicant_people_information_id": applicant_id
    }

    payload = build_payload(detail, generic_value_resolver, overrides)

    http_put(
        f"/invt/{invt_id}/form/applicant/data/save?",
        {"data": payload},
    )

    print("[APPLICANT] Saved successfully")