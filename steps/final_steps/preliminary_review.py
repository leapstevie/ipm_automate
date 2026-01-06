import os
import random
import requests
from datetime import date
from typing import Optional, Dict, Any, Callable

from config import QIP_BASE_URL 

try:
    from sqlalchemy import desc
    from app.core.system.db import SessionQipLocal
    from app.models.qip.user_model import USER_SESSION_MODEL
except ImportError:
    SessionQipLocal = None
    USER_SESSION_MODEL = None
    desc = None
    print("⚠️ Warning: DB modules not found. DB token login will be disabled.")


# ============================================================
# Constants / Configuration
# ============================================================

FLOW1_STAGE_KEY = 2

PHONE_RULES = {
    "012860067": {"only_stages": {2, 7}, "do_site_visit_pre_steps": True},
}

STAGE_CONFIG = {
    2: {"name": "Preliminary Review",          "users": ["017581166", "093282238", "012910678", "012860067"], "target_flow": 3},
    3: {"name": "Mission Approval",            "users": ["099902345"],                                    "target_flow": 4},
    4: {"name": "OSS Meeting Request",         "users": ["012345692"],                                    "target_flow": 5},
    5: {"name": "OSS Meeting Approval",        "users": ["012916188"],                                    "target_flow": 6},
    6: {"name": "Site Visit Comments",         "users": ["047770008"],                                    "target_flow": 7},
    7: {"name": "Site Visit Report Draft",     "users": ["012860067"],                                    "target_flow": 8},
    8: {"name": "Site Visit Report Submit",    "users": ["099902345"],                                    "target_flow": 9},
    9: {"name": "Incentive Proposal Draft",    "users": ["093282238"],                                    "target_flow": 10},
    10: {"name": "Incentive Proposal Request", "users": ["012865228"],                                    "target_flow": 11},
    11: {"name": "Incentive Proposal Review",  "users": ["099902345"],                                    "target_flow": 12},
    12: {"name": "Incentive Pre-Approval",     "users": ["012345692"],                                    "target_flow": 13},
    13: {"name": "Incentive Approval",         "users": ["012916188"],                                    "target_flow": 13},
}

MISSION_CHAIR = "7222f2c2-ba81-4393-9443-7bd6af13bd52"
MISSION_SEC_COMMENT = "8cefdc21-3068-4b13-a671-d4d1d789619c"

CHAIR_USER = {
    "user_id": "e84fc28a-34e8-4fb4-b9e6-3e236508ed20",
    "salute": "daaeb978-104f-4684-a958-48fb8440edbb",
    "firstname": "វិសុទ្ធ",
    "lastname": "មឿង",
    "phone_code": "855",
    "phone_number": "12860067",
    "position": "ប្រធាននាយកដ្ឋានស្តីទី",
    "department": "8ddcadea-d98b-4d5d-b0da-2e654248bb4e",
}

SEC_COMMENT_USER = {
    "user_id": "5b6c8ebd-0947-4741-bac3-50626186af2f",
    "salute": "daaeb978-104f-4684-a958-48fb8440edbb",
    "firstname": "ស៊ីថា",
    "lastname": "គង់",
    "phone_code": "855",
    "phone_number": "47770008",
    "position": "តំណាង",
    "department": "1f3a211b-bee4-4810-86bb-d93fa14601b8",
}


# ============================================================
# Helpers / Utilities
# ============================================================

def api_BASE() -> str:
    base = str(QIP_BASE_URL).rstrip("/")
    return base if base.endswith("/api/v1") else f"{base}/api/v1"


def _env_password() -> str:
    pwd = os.getenv("DEFAULT_QIP_USER_PASSWORD", "").strip() or os.getenv("User_pass", "").strip()
    if not pwd:
        raise RuntimeError("No password found in env (DEFAULT_QIP_USER_PASSWORD or User_pass)")
    return pwd


def _json_data(resp: requests.Response) -> dict:
    return resp.json() if resp is not None and resp.content else {}


def check_resp(resp: requests.Response, step: str, payload: Any = None) -> None:
    if resp.status_code >= 400:
        print(f"\n❌ [{step}] {resp.status_code} {resp.url}")
        if payload is not None:
            print("Payload:", payload)
        print("Response:", resp.text[:2000])
        resp.raise_for_status()


# ============================================================
# Data model
# ============================================================

class UserContext:
    def __init__(self, phone: str):
        self.user_id = phone
        self.email = None
        self.phone_code = "855"
        self.phone_number = phone.lstrip("0")


# ============================================================
# Auth Manager
# ============================================================

class AuthManager:
    @staticmethod
    def try_db_tokens(user_row: UserContext) -> Optional[Dict[str, str]]:

        if not SessionQipLocal or not USER_SESSION_MODEL or not desc:
            return None

        username = user_row.phone_number
        if not username:
            return None

        session = SessionQipLocal()
        try:
            tokens = (
                session.query(USER_SESSION_MODEL.access_token)
                .filter(USER_SESSION_MODEL.username == username)
                .filter(USER_SESSION_MODEL.status_id == 1)
                .order_by(desc(USER_SESSION_MODEL.latest_requested_datetime))
                .all()
            )

            for (token,) in tokens:
                if not token:
                    continue

                headers = {
                    "Authorization": f"Bearer {token}",
                    "Accept": "*/*",
                    "Content-Type": "application/json",
                }

                try:
                    r = requests.get(f"{api_BASE()}/users/me", headers=headers, timeout=5)
                    if r.status_code == 200:
                        return headers
                except Exception:
                    pass

            return None

        except Exception as e:
            print(f"⚠️ DB token check failed: {e}")
            return None

        finally:
            try:
                session.close()
            except Exception:
                pass

    @staticmethod
    def login_with_password(user_row: UserContext) -> Dict[str, str]:
      
        url = f"{api_BASE()}/auth/login"
        pwd = _env_password()

        candidates = [user_row.email, user_row.phone_number]
        candidates = [str(c) for c in candidates if c]

        phone_code = str(user_row.phone_code or "855").strip()
        last_error: Optional[str] = None

        for username in candidates:
            try:
                res = requests.post(
                    url,
                    json={"phone_code": phone_code, "username": username, "password": pwd},
                    headers={"Accept": "*/*"},
                    timeout=100,
                )
                if res.status_code == 200:
                    token = (_json_data(res).get("data") or {}).get("access_token")
                    if token:
                        return {
                            "Authorization": f"Bearer {token}",
                            "Accept": "*/*",
                            "Content-Type": "application/json",
                        }
                last_error = f"{res.status_code} {res.text}"
            except requests.RequestException as e:
                last_error = str(e)

        raise RuntimeError(f"Failed login user_id={user_row.user_id}. Last: {last_error}")

    @classmethod
    def login(cls, user_row: UserContext) -> Dict[str, str]:
        # 1) Try DB token reuse
        headers = cls.try_db_tokens(user_row)
        if headers:
            return headers

        # 2) Fallback to password
        return cls.login_with_password(user_row)

    @classmethod
    def run_as_user(cls, user_row: UserContext, fn: Callable[[Dict[str, str]], Any]) -> Any:
        headers = cls.login(user_row)
        return fn(headers)


# ============================================================
# Site Visit Manager
# ============================================================

class SiteVisitManager:
    @staticmethod
    def _extract_site_visit_id(resp_json: dict, fallback: str) -> str:
        data = (resp_json or {}).get("data") or {}
        if isinstance(data, dict):
            val = data.get("site_visit_id") or data.get("id")
            if val:
                return str(val)

            sv = data.get("site_visit")
            if isinstance(sv, dict) and sv.get("id"):
                return str(sv["id"])

        return fallback

    @classmethod
    def post_site_visit_composition_twice(cls, sess: requests.Session, invt_id: str) -> dict:
        url = f"{api_BASE()}/site_visit/{invt_id}/composition"

        r1 = sess.post(url, json={**CHAIR_USER, "mission_position": MISSION_CHAIR}, timeout=60)
        check_resp(r1, "site_visit.composition.chair")
        sv_id = cls._extract_site_visit_id(_json_data(r1), fallback=invt_id)

        r2 = sess.post(url, json={**SEC_COMMENT_USER, "mission_position": MISSION_SEC_COMMENT}, timeout=60)
        check_resp(r2, "site_visit.composition.sec_comment")
        sv_id = cls._extract_site_visit_id(_json_data(r2), fallback=sv_id)
        

        return {"site_visit_id": sv_id}

    @classmethod
    def do_pre_steps(cls, sess: requests.Session, invt_id: str) -> dict:
        today = date.today().isoformat()

        r = sess.get(f"{api_BASE()}/site_visit/composition/form_v2", params={"invt_id": invt_id}, timeout=100)
        check_resp(r, "site_visit.form_v2")

        comp = cls.post_site_visit_composition_twice(sess, invt_id)
        site_visit_id = comp["site_visit_id"]

        url_draft = f"{api_BASE()}/site_visit/{site_visit_id}/draft"
        r = sess.get(url_draft, timeout=100)
        check_resp(r, "site_visit.draft.get")

        r = sess.put(
            url_draft,
            json={
                "start_date": today,
                "check_date": today,
                "return_date": today,
                "note": "",
                "document_attachment": "",
                "transportation": "",
            },
            timeout=60,
        )
        check_resp(r, "site_visit.draft.put")

        url_report = f"{api_BASE()}/site_visit_report/{site_visit_id}"
        r = sess.get(url_report, timeout=100)
        check_resp(r, "site_visit_report.get")

        r = sess.put(
            url_report,
            json={
                "check_date": today,
                "committy_comments": [],
                "composition_lead": "គម្រោងវិនិយោគនេះមានគោលបំណងអភិវឌ្ឍអចលនទ្រព្យសម្រាប់ការប្រើប្រាស់ពាណិជ្ជកម្ម និងលំនៅឋាន ដោយផ្អែកលើទីតាំងមានសក្ដានុពល និងតម្រូវការទីផ្សារកំពុងកើនឡើង។",
                "conclusion_comment": "<p>ដោយផ្អែកលើការពិនិត្យទីតាំង ស្ថានភាពទីផ្សារ និងឯកសារពាក់ព័ន្ធ គម្រោងនេះត្រូវបានវាយតម្លៃថាមានភាពអាចអនុវត្តបាន។ ទោះជាយ៉ាងណា សូមអនុវត្តការត្រួតពិនិត្យផ្នែកច្បាប់ និងហិរញ្ញវត្ថុបន្ថែម មុនធ្វើសេចក្ដីសម្រេចចុងក្រោយ។</p>",
                "contract_rent": "កិច្ចសន្យាជួលមានរយៈពេល 15 ឆ្នាំ ជាមួយលក្ខខណ្ឌកែសម្រួលថ្លៃជួលរៀងរាល់ 3 ឆ្នាំម្តង ដោយផ្អែកលើស្ថានភាពទីផ្សារ។",
                "investment_location": "សង្កាត់ទន្លេបាសាក់ ខណ្ឌចំការមន រាជធានីភ្នំពេញ",
                "land_doc": "ដីមានប័ណ្ណកម្មសិទ្ធិប្រភេទ Hard Title ចេញដោយក្រសួងរៀបចំដែនដី នគរូបនីយកម្ម និងសំណង់។",
                "location_situation": "ទីតាំងស្ថិតនៅជិតផ្លូវធំ មានហេដ្ឋារចនាសម្ព័ន្ធល្អ ងាយស្រួលចូលដំណើរការ និងជិតតំបន់ពាណិជ្ជកម្មសំខាន់ៗ។",
                "office_location": "ការិយាល័យគម្រោង ស្ថិតនៅអគារលេខ 45 ផ្លូវ 271 ខណ្ឌចំការមន រាជធានីភ្នំពេញ",
                "site_visit_info": "<p>ក្រុមការងារបានចុះពិនិត្យទីតាំងនៅថ្ងៃទី 2025-12-27 ហើយបានបញ្ជាក់ថា ទីតាំងពិតប្រាកដត្រូវនឹងឯកសារផ្លូវការ និងមិនមានវិវាទបច្ចុប្បន្ន។</p>",
            },
            timeout=60,
        )
        check_resp(r, "site_visit_report.put")

        return {"site_visit_id": site_visit_id}


# ============================================================
# Flow Automation
# ============================================================

class FlowAutomation:
    @staticmethod
    def should_run_phone_on_stage(phone: str, stage_key: int) -> bool:
        rule = PHONE_RULES.get(phone)
        if not rule:
            return True

        only_stages = rule.get("only_stages")
        if only_stages is not None:
            return stage_key in only_stages

        only_stage = rule.get("only_stage")
        return (only_stage is None) or (stage_key == only_stage)

    @staticmethod
    def maybe_run_phone_pre_steps(sess: requests.Session, invt_id: str, phone: str, stage_key: int) -> None:
        rule = PHONE_RULES.get(phone) or {}
        if rule.get("do_site_visit_pre_steps") and stage_key == FLOW1_STAGE_KEY:
            try:
                SiteVisitManager.do_pre_steps(sess, invt_id)
            except Exception as e:
                print(f"⚠️ site_visit pre-steps failed or already done: {e}")

    @staticmethod
    def fetch_confirmation(headers: dict, invt_id: str) -> dict:
        r = requests.get(f"{api_BASE()}/invt/{invt_id}/confirmation", headers=headers, timeout=100)
        check_resp(r, "flow.confirmation")
        return _json_data(r)

    @staticmethod
    def stage_needs_action(confirm_json: dict, stage_key: int) -> bool:
        data = (confirm_json or {}).get("data") or {}

        current = ((data.get("stage_info") or {}).get("current"))
        if current != stage_key:
            return False

        nodes = data.get("flow_nodes") or []
        for node in nodes:
            if node.get("flow_order") != stage_key:
                continue

            if node.get("is_completed") == 1:
                return False

            actions = node.get("flow_item_detail_actions") or []
            if not actions:
                return True

            for a in actions:
                if (a.get("updated_action") in (None, "")) and (a.get("updated_by_user") is None):
                    return True

            return True

        return True

    @staticmethod
    def pick_signature_id(options, prefer_delegated_to_sg: bool = False) -> Optional[str]:
        if not options:
            return None

        if isinstance(options[0], str):
            return options[0]

        delegated = None
        direct = None
        for o in options:
            if not isinstance(o, dict):
                continue
            if o.get("assignment_to_sign_on_certificate_from_dpm"):
                delegated = delegated or o
            else:
                direct = direct or o

        picked = delegated if prefer_delegated_to_sg else direct
        picked = picked or direct or delegated or (options[0] if isinstance(options[0], dict) else None)

        if isinstance(picked, dict):
            return picked.get("id") or picked.get("value")
        return None

    @classmethod
    def submit_preliminary(
        cls,
        invt_id: str,
        headers: dict,
        target_flow_order: int = 3,
        phone: Optional[str] = None,
        stage_key: Optional[int] = None,
        prefer_delegated_to_sg: bool = False,
        is_return: bool = False,
    ):
        
        sess = requests.Session()
        sess.headers.update(headers)
        try:
            if phone and stage_key is not None and not is_return:
                cls.maybe_run_phone_pre_steps(sess, invt_id, phone, stage_key)

            # Confirmation
            res_c = sess.get(f"{api_BASE()}/invt/{invt_id}/confirmation", timeout=100)
            check_resp(res_c, "flow.confirmation")
            data = (_json_data(res_c).get("data") or {})
            action_form = data.get("action_form") or {}

            # Signature preference
            sigs = [
                s.get("signature", {}).get("id")
                for s in (data.get("preference_signatures") or [])
                if isinstance(s, dict)
            ]
            selected_sig = random.choice([s for s in sigs if s]) if sigs else None
            if is_return:
                selected_sig = None

            # Comment preference
            comments = [c.get("comment") for c in (data.get("preference_comments") or []) if isinstance(c, dict)]
            selected_comment = random.choice([c for c in comments if c]) if comments else "ក្រុមហ៊ុនបានរៀបចំលក្ខន្តិកៈអាចទទួលយកបាន។"
            if is_return:
                selected_comment = "សូមពិនិត្យកែតម្រូវឡើងវិញ"

            signature_on_cert_options = action_form.get("signature_on_certificate") or []
            signature_on_certificate_id = cls.pick_signature_id(signature_on_cert_options, prefer_delegated_to_sg)

            payload = {
                "attachment": None,
                "attachment_irc": None,
                "attachment_letter": None,
                "attachment_notification": None,
                "attachment_report": None,
                "certificate_related_document": {"new_docs": [], "remove_docs": []},
                "comment": selected_comment,
                "letter_related_document": {"new_docs": [], "remove_docs": []},
                "notification_related_document": {"new_docs": [], "remove_docs": []},
                "preference_attachment_report_id": None,
                "preference_signature_id": selected_sig,
                "signature": None,
                "signature_on_certificate": None,
                "submit_for_one_stop_meeting": 0,
                "flow_order": target_flow_order,
            }

            if is_return:
                payload.pop("submit_for_one_stop_meeting", None)
                payload["return_for_one_stop_meeting"] = 0

            if stage_key == 13:
                if not signature_on_certificate_id:
                    raise RuntimeError("Stage 13 requires signature_on_certificate, but it is empty.")
                payload["signature_on_certificate"] = signature_on_certificate_id

            if is_return:
                url = f"{api_BASE()}/investment_project/{invt_id}/flow/return?step_code=approval_flow&project_type=qip"
            else:
                url = f"{api_BASE()}/investment_project/{invt_id}/flow/submit?step_code=approval_flow&project_type=qip"

            res_s = sess.put(url, json=payload, timeout=60)
            check_resp(res_s, "flow.return" if is_return else "flow.submit", payload)
            return _json_data(res_s) or True

        finally:
            try:
                sess.close()
            except Exception:
                pass


# ============================================================
# Flow Runner
# ============================================================

def get_current_stage(invt_id: str, user_row: UserContext) -> Optional[int]:
    def _fetch_stage(headers: dict) -> Optional[int]:
        try:
            res = requests.get(f"{api_BASE()}/invt/{invt_id}/confirmation", headers=headers, timeout=100)
            if res.status_code == 200:
                data = (_json_data(res).get("data") or {})
                stage_info = data.get("stage_info") or {}
                return stage_info.get("current")
        except Exception:
            pass
        return None

    return AuthManager.run_as_user(user_row, _fetch_stage)


def submit_flow_all_departments(invt_id: str, return_config: Optional[dict] = None) -> bool:
    checker_user = UserContext(STAGE_CONFIG[FLOW1_STAGE_KEY]["users"][0])

    max_loops = 20
    has_triggered_return = False

    for loop_count in range(max_loops):
        current_flow = get_current_stage(invt_id, checker_user)
        print(f"ℹ️ Current Flow Order: {current_flow}")

        if not current_flow:
            print("⚠️ Could not determine current flow order. Exiting.")
            return False

        # -------------------------
        # RETURN logic (only once)
        # -------------------------
        if return_config and not has_triggered_return:
            trigger_stage = return_config.get("trigger")
            target_stage = return_config.get("target")

            if current_flow == trigger_stage and target_stage:
                print(f"🔄 Return Triggered at Stage {current_flow} -> Target {target_stage}")

                config = STAGE_CONFIG.get(current_flow) or {}
                phones = config.get("users") or []

                return_user_phone = next(
                    (p for p in phones if FlowAutomation.should_run_phone_on_stage(p, current_flow)),
                    None
                )

                if not return_user_phone:
                    print(f"⚠️ No eligible user found for return at stage {current_flow}")
                else:
                    user_row = UserContext(return_user_phone)

                    def _perform_return(headers: dict) -> Any:
                        confirm_data = FlowAutomation.fetch_confirmation(headers, invt_id)
                        action_form = (confirm_data.get("data") or {}).get("action_form") or {}
                        return_stages = action_form.get("return_stage") or []

                        allowed_orders = [rs.get("flow_order") for rs in return_stages if isinstance(rs, dict)]
                        if target_stage not in allowed_orders:
                            print(f"⚠️ Target stage {target_stage} not allowed. Allowed: {allowed_orders}")
                            return False

                        return FlowAutomation.submit_preliminary(
                            invt_id,
                            headers,
                            target_flow_order=target_stage,
                            phone=return_user_phone,
                            stage_key=current_flow,
                            is_return=True,
                        )

                    try:
                        res = AuthManager.run_as_user(user_row, _perform_return)
                        if res:
                            print(f"✅ Return successful to stage {target_stage}")
                            has_triggered_return = True
                            print(f"🛑 Stopping automation after return to stage {target_stage}.")
                            return True
                    except Exception as e:
                        print(f"❌ Return failed: {e}")

        # -------------------------
        # NORMAL forward flow
        # -------------------------
        config = STAGE_CONFIG.get(current_flow)
        if not config:
            print(f"✅ No automation config for flow order {current_flow}. Finished or unknown stage.")
            return True

        confirm = AuthManager.run_as_user(checker_user, lambda h: FlowAutomation.fetch_confirmation(h, invt_id))
        if not FlowAutomation.stage_needs_action(confirm, current_flow):
            print(f"✅ Stage {current_flow} already completed / no pending action. Stop.")
            return True

        target_flow = config["target_flow"]
        print(f"🚀 Processing Stage -> next: {target_flow}")

        phones = config.get("users") or []
        ran_any = False

        for phone in phones:
            if not FlowAutomation.should_run_phone_on_stage(phone, current_flow):
                only = (PHONE_RULES.get(phone) or {}).get("only_stages") or (PHONE_RULES.get(phone) or {}).get("only_stage")
                print(f"⏭️ Skip {phone}: only allowed on stage {only}")
                continue

            ran_any = True
            user_row = UserContext(phone)

            AuthManager.run_as_user(
                user_row,
                lambda headers, _phone=phone, _target=target_flow, _stage=current_flow:
                    FlowAutomation.submit_preliminary(
                        invt_id,
                        headers,
                        target_flow_order=_target,
                        phone=_phone,
                        stage_key=_stage,
                        is_return=False,
                    ),
            )

            stage_name = (STAGE_CONFIG.get(target_flow) or {}).get("name", "")
            print(f"✅ ready: {target_flow} stage {stage_name} (User: {phone})")

        if not ran_any:
            print(f"🛑 No eligible users for flow {current_flow}. Please update STAGE_CONFIG[{current_flow}]['users'].")
            return False

    return True


# ============================================================
# Public entrypoints
# ============================================================

def submit_flow(invt_id: str, user_id: Optional[str] = None, return_config: Optional[dict] = None) -> bool:
    return submit_flow_all_departments(invt_id, return_config=return_config)
