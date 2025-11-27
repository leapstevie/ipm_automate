from api.http import http_get, http_put
from api.upload import upload_temp_attachment
from utils.applicant import get_primary_applicant_id


def submit_board_member(invt_id, applicant_id=None):
    
    # ----------------------------------------
    # 1) Decide applicant ID (always keep consistent)
    # ----------------------------------------
    applicant_id = applicant_id or get_primary_applicant_id(invt_id)

    # ----------------------------------------
    # 2) Simulate UI click (open applicant popup)
    # ----------------------------------------
    
    http_get(
        f"/invt/{invt_id}/popup_subform/f_invt_project_applicant_information",
        params={"object_id": applicant_id},
    )
    
    # ----------------------------------------
    # 3) Load board_member row
    # ----------------------------------------
    
    bm_data = http_get(f"/invt/{invt_id}/subform/board_member")["data"]
    objects = bm_data.get("objects") or []

    # ----------------------------------------
    # 4) If no row exists, create an empty one
    # ----------------------------------------
    
    if not objects:
        http_put(
            f"/invt/{invt_id}/subform/board_member/data/save?",
            {"data": [{}]},
        )
        bm_data = http_get(f"/invt/{invt_id}/subform/board_member")["data"]
        objects = bm_data.get("objects") or []
        
    # ----------------------------------------
    # 5) Select row ID
    # ----------------------------------------
    board_member_id = (
        objects[0]["id"]
        if objects else bm_data["investment_info"]["object_id"]
    )
    police_record_file = upload_temp_attachment("picture_automate/images.jpeg")
    
    payload = [
        {"field_code": "board_member_board_invt_applicant_people_information_id", "value": applicant_id,         "comment": None},
        {"field_code": "police_record_attachment_id",                             "value": police_record_file,   "comment": None},
        {"field_code": "board_member_authorized_position_code_to_sign",           "value": "manager",            "comment": None},
        {"field_code": "board_member_note",                                       "value": "sdadad",             "comment": None},
    ]

    # 6) Save board member
    http_put(
        f"/invt/{invt_id}/subform/board_member/object/{board_member_id}/data/save?",
        {"data": payload},
    )

    return True
