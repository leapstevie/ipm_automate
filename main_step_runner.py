# run_all_steps.py

from steps.generic_step import submit_generic_step
from steps.company_composition import submit_company_composition
from steps.board_member import submit_board_member
from steps.applicant import submit_applicant_step
import requests
from config import HEADERS


def run_all_steps(invt_id):
    res = requests.get("http://dev-api-ipm.cdc.gov.kh/api/v2/step", headers=HEADERS)
    steps = sorted(res.json()["data"]["qip"], key=lambda x: x.get("step_order", 0))

    print("\n========== START RUNNING ALL STEPS ==========")

    fixed_applicant_id = None  # MASTER applicant ID for entire flow

    for step in steps:
        code = step["code"]
        print(f"\n>>> PROCESSING STEP: {code}")

        # STEP 1 — company_composition generates the ONLY applicant_id
        if code == "company_composition":
            fixed_applicant_id = submit_company_composition(invt_id)
            print(f"[MASTER] applicant_id = {fixed_applicant_id}")
            continue

        # STEP 2 — board_member always uses same applicant_id
        if code == "board_member_composition":
            submit_board_member(invt_id, fixed_applicant_id)
            continue

        # STEP 3 — applicant form always uses same applicant_id
        if code == "applicant":
            submit_applicant_step(invt_id, fixed_applicant_id)
            continue

        # All other steps → generic handler
        submit_generic_step(invt_id, code)

    print("\n========== ALL STEPS COMPLETED ==========")
