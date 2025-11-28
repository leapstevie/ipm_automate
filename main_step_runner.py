# run_all_steps.py

import requests
from config import HEADERS
from steps.generic_step import submit_generic_step
from steps.approval_flow import submit_signature


def run_all_steps(invt_id):
    res = requests.get("http://dev-api-ipm.cdc.gov.kh/api/v2/step", headers=HEADERS)
    steps = sorted(res.json()["data"]["qip"], key=lambda x: x.get("step_order", 0))

    print("\n========== START RUNNING ALL STEPS ==========")

    for step in steps:
        code = step["code"]
        print(f"\n>>> PROCESSING STEP: {code}")
        submit_generic_step(invt_id, code)

    # sign at the end
    submit_signature(invt_id)

    print("\n========== ALL STEPS + SIGNATURE COMPLETED ==========")
