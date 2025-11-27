import requests
import json
from config import BASE, HEADERS

def http_get(path, params=None):
    res = requests.get(BASE + path, headers=HEADERS, params=params)
    res.raise_for_status()
    return res.json()

def http_put(path, data=None):
    url = BASE + path
    print("\n==================== PUT DEBUG ====================")
    print("URL:", url)
    print("BODY:", json.dumps(data, ensure_ascii=False, indent=2))
    res = requests.put(url, headers=HEADERS, json=data)
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)
    print("===================================================\n")

    if res.status_code == 400:
        try:
            body = res.json()
        except:
            raise Exception(f"PUT ERROR 400 (non-JSON): {res.text}")

        log_id = body.get("log_id")
        code = body.get("code")
        msg = (body.get("message") or {}).get("en") or body.get("message")

        # 👇 NEW: print any field-level info backend gives you
        details = body.get("data")
        if details:
            print("VALIDATION DETAILS:")
            print(json.dumps(details, indent=2, ensure_ascii=False))

        raise Exception(f"VALIDATION 400 (code={code}, log_id={log_id}): {msg}")

def http_post(path, body):
    url = BASE + path

    print("\n==================== POST DEBUG ====================")
    print("URL:", url)
    print("BODY:", json.dumps(body, indent=2, ensure_ascii=False))

    res = requests.post(
        url,
        headers={**HEADERS, "Content-Type": "application/json"},
        json=body
    )

    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)
    print("===================================================\n")

    if res.status_code >= 400:
        raise Exception(f"POST ERROR {res.status_code}: {res.text}")

    try:
        return res.json()
    except:
        return None