# steps/board_member.py

from api.http import http_get, http_put
from api.upload import upload_temp_attachment


def submit_board_member(invt_id, applicant_id):

    print(f"[BOARD] Using applicant_id = {applicant_id}")

    # Simulate UI click
    http_get(
        f"/invt/{invt_id}/popup_subform/f_invt_project_applicant_information",
        params={"object_id": applicant_id},
    )

    # Load existing row
    bm = http_get(f"/invt/{invt_id}/subform/board_member")["data"]
    objs = bm.get("objects") or []

    if not objs:
        http_put(
            f"/invt/{invt_id}/subform/board_member/data/save?",
            {"data": [{}]},
        )
        bm = http_get(f"/invt/{invt_id}/subform/board_member")["data"]
        objs = bm.get("objects") or []

    board_id = objs[0]["id"]

    police = upload_temp_attachment("picture_automate/images.jpeg")

    payload = [
        {"field_code": "board_member_board_invt_applicant_people_information_id", "value": applicant_id},
        {"field_code": "police_record_attachment_id", "value": police},
        {"field_code": "board_member_authorized_position_code_to_sign", "value": "manager"},
        {"field_code": "board_member_note", "value": "AUTO_NOTE"},
    ]

    http_put(
        f"/invt/{invt_id}/subform/board_member/object/{board_id}/data/save?",
        {"data": payload},
    )

    print("[BOARD] Saved successfully")
