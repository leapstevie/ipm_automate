# utils/applicant.py

from api.http import http_get, http_put
from utils.random_data import generic_value_resolver
from utils.schema_payload import build_payload

_PRIMARY_APPLICANT_CACHE = {}


def get_applicant_object_id(invt_id):
    data = http_get(
        f"/invt/{invt_id}/popup_subform/f_invt_project_applicant_information"
    )["data"]

    objects = data.get("objects") or []

    if not objects:
        return data["investment_info"]["object_id"]

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

    rdm = {}
    return build_payload(detail, generic_value_resolver, rdm)


def get_shareholder_applicant_id(invt_id):
    data = http_get(f"/invt/{invt_id}/subform/share_holder")["data"]
    objs = data.get("objects") or []

    if objs and objs[0].get("form_data"):
        return objs[0]["form_data"].get(
            "share_holder_invt_applicant_people_information_id"
        )

    return None


def ensure_primary_applicant(invt_id):
    if invt_id in _PRIMARY_APPLICANT_CACHE:
        return _PRIMARY_APPLICANT_CACHE[invt_id]

    sh = get_shareholder_applicant_id(invt_id)
    if sh:
        _PRIMARY_APPLICANT_CACHE[invt_id] = sh
        return sh

    applicant_id = get_applicant_object_id(invt_id)

    popup = http_get(
        f"/invt/{invt_id}/popup_subform/f_invt_project_applicant_information",
        params={"object_id": applicant_id},
    )["data"]

    detail = popup.get("detail") or {}

    payload = build_default_applicant_payload(invt_id, detail)

    http_put(
        f"/invt/{invt_id}/popup_subform/"
        f"f_invt_project_applicant_information/object/{applicant_id}/data/save?",
        {"data": payload},
    )

    print("Applicant popup saved successfully.")

    _PRIMARY_APPLICANT_CACHE[invt_id] = applicant_id
    return applicant_id


def get_primary_applicant_id(invt_id):
    return ensure_primary_applicant(invt_id)
