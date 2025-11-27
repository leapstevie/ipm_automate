from api.http import http_get
from utils.random_data import (
    random_phone_code,
    random_phone,
    random_email,
    random_address,
    generic_value_resolver
)
from utils.schema_payload import build_payload


def get_applicant_object_id(invt_id):
    data = http_get(
        f"/invt/{invt_id}/popup_subform/f_invt_project_applicant_information"
    )["data"]

    objects = data.get("objects") or []

    if not objects:
        return data["investment_info"]["object_id"]

    # Find row with form_data
    for obj in objects:
        if obj.get("form_data"):
            return obj["id"]

    return objects[0]["id"]


def build_default_applicant_payload(invt_id, detail):
    print("=== APPLICANT FIELD CODES RECEIVED FROM SERVER ===")
    for panel in detail.get("panels", []):
        for group in panel.get("field_groups", []):
            for field in group.get("fields", []):
                print(" ->", field.get("code"))
    print("========================================")

    rdm = {
        "phone_code": random_phone_code(),
        "phone_number": random_phone(),
        "email": random_email(),
        "address": random_address(),
    }

    return build_payload(detail, generic_value_resolver, rdm)


def get_shareholder_applicant_id(invt_id):
    data = http_get(f"/invt/{invt_id}/subform/share_holder")["data"]
    objs = data.get("objects") or []

    if objs and objs[0].get("form_data"):
        return objs[0]["form_data"].get(
            "share_holder_invt_applicant_people_information_id"
        )

    return None


def get_primary_applicant_id(invt_id):
    sh = get_shareholder_applicant_id(invt_id)
    if sh:
        return sh

    return get_applicant_object_id(invt_id)



