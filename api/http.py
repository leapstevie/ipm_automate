import json
import requests
from config import QIP_BASE_URL 
from tokens import token_manager


def _mk_url(path: str) -> str:
    base = (QIP_BASE_URL or "").rstrip("/")
    p = (path or "")
    if not p.startswith("/"):
        p = "/" + p
    return base + p



def _request(method: str, url: str, *, user_id=None, params=None, json_body=None, files=None, data=None, timeout=460):

    res = requests.request(
        method,
        url,
        headers=token_manager.headers(user_id=user_id),
        params=params,
        json=json_body,
        files=files,
        data=data,
        timeout=timeout,
    )

    if res.status_code in (401, 403):
        token_manager.on_unauthorized(user_id=user_id)
        res = requests.request(
            method,
            url,
            headers=token_manager.headers(user_id=user_id),
            params=params,
            json=json_body,
            files=files,
            data=data,
            timeout=timeout,
        )

    return res


def http_get(path, params=None, *, user_id=None, timeout=460):
    url = _mk_url(path)
    res = _request("GET", url, user_id=user_id, params=params, timeout=timeout)
    res.raise_for_status()
    return res.json()


def http_post(path, body, *, user_id=None, timeout=460):
    url = _mk_url(path)

    print("\n==================== POST DEBUG ====================")
    print("URL:", url)
    print("BODY:", json.dumps(body, indent=2, ensure_ascii=False))

    res = _request("POST", url, user_id=user_id, json_body=body, timeout=timeout)

    print("STATUS:", res.status_code)
    # print("RESPONSE:", res.text)
    print("===================================================\n")

    if res.status_code >= 400:
        raise Exception(f"POST ERROR {res.status_code}: {res.text}")

    return res.json()


def http_put(path, data=None, *, user_id=None, timeout=460):
    url = _mk_url(path)

    print("\n==================== PUT DEBUG ====================")
    print("URL:", url)
    print("BODY:", json.dumps(data, ensure_ascii=False, indent=2))

    res = _request("PUT", url, user_id=user_id, json_body=data, timeout=timeout)

    print("STATUS:", res.status_code)
    # print("RESPONSE:", res.text)
    print("===================================================\n")

    if res.status_code == 400:
        try:
            body = res.json()
        except Exception:
            raise Exception(f"PUT ERROR 400 (non-JSON): {res.text}")

        log_id = body.get("log_id")
        code = body.get("code")
        msg = (body.get("message") or {}).get("en") or body.get("message")

        details = body.get("data")
        if details:
            print("VALIDATION DETAILS:")
            print(json.dumps(details, indent=2, ensure_ascii=False))

        raise Exception(f"VALIDATION 400 (code={code}, log_id={log_id}): {msg}")

    res.raise_for_status()
    return res.json()
