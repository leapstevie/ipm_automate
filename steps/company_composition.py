# steps/company_composition.py

from api.http import http_get, http_put
from utils.random_data import generic_value_resolver
from utils.schema_payload import build_payload
from utils.applicant import (
    get_applicant_object_id,
    build_default_applicant_payload,
    get_shareholder_applicant_id,
)
from api.upload import upload_temp_attachment


def submit_company_composition(invt_id):

    # 1) Determine applicant_id (always FIRST TIME)
    applicant_id = get_shareholder_applicant_id(invt_id)
    if not applicant_id:
        applicant_id = get_applicant_object_id(invt_id)

    # 2) Load applicant popup schema
    popup = http_get(
        f"/invt/{invt_id}/popup_subform/f_invt_project_applicant_information",
        params={"object_id": applicant_id},
    )["data"]

    detail = popup["detail"]

    # 3) Build applicant payload
    applicant_payload = build_default_applicant_payload(invt_id, detail)

    http_put(
        f"/invt/{invt_id}/popup_subform/"
        f"f_invt_project_applicant_information/object/{applicant_id}/data/save?",
        {"data": applicant_payload},
    )

    print("[COMPANY] Applicant saved")

    # 4) Shareholder subform
    sh_data = http_get(f"/invt/{invt_id}/subform/share_holder")["data"]
    share_id = (sh_data.get("objects") or [{}])[0].get("id") \
               or sh_data.get("investment_info", {}).get("object_id")

    sh_detail = http_get(
        f"/invt/{invt_id}/subform/share_holder",
        params={"object_id": share_id},
    )["data"]["detail"]

    # Force applicant_id into shareholder
    overrides = {
        "share_holder_invt_applicant_people_information_id": applicant_id
    }

    shareholder_payload = build_payload(sh_detail, generic_value_resolver, overrides)

    http_put(
        f"/invt/{invt_id}/subform/share_holder/object/{share_id}/data/save?",
        {"data": shareholder_payload},
    )

    print("[COMPANY] Shareholder saved")
    print("[COMPANY] Company Composition completed")

    return applicant_id  
