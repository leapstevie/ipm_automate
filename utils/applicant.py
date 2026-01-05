# utils/applicant.py

from api.http import http_get, http_put
from utils.random_data import generic_value_resolver
from utils.schema_payload import build_payload


_PRIMARY_APPLICANT_CACHE = {}   


def _fetch_applicant_subform(invt_id):
    return http_get(
        f"/invt/{invt_id}/popup_subform/f_invt_project_applicant_information"
    )["data"]


def _extract_existing_applicant_id(data):
    objects = data.get("objects") or []
    for obj in objects:
        if obj.get("form_data"):
            return obj["id"]
    if objects:
        return objects[0]["id"]
    return data["investment_info"]["object_id"]


def build_default_applicant_payload(invt_id, detail):
    return build_payload(detail, generic_value_resolver, {})

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

    subform_data = _fetch_applicant_subform(invt_id)
    applicant_id = _extract_existing_applicant_id(subform_data)

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

    _PRIMARY_APPLICANT_CACHE[invt_id] = applicant_id
    return applicant_id


def get_primary_applicant_id(invt_id):
    return ensure_primary_applicant(invt_id)


# ---------------------------------------------------------
# NEW: simple controller for generating N applicants
# ---------------------------------------------------------

def add_multiple_applicants(invt_id, count=1):
    created = []
    for _ in range(count):

        subform = _fetch_applicant_subform(invt_id)
        obj_id = _extract_existing_applicant_id(subform)
        payload = build_payload()

        http_put(
            f"/invt/{invt_id}/popup_subform/"
            f"f_invt_project_applicant_information/object/{obj_id}/data/save?",
            {"data": payload},
        )

        created.append(obj_id)

    return created
