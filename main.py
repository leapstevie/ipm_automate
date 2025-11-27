from main_step_runner import run_all_steps
from api.http import http_get


def create_application():
    res = http_get("/step/general_info", params={"type": "qip"})
    return res["data"]["investment_info"]["id"]


def main():
    invt_id = create_application()
    print("New application:", invt_id)

    run_all_steps(invt_id)


if __name__ == "__main__":
    main()
