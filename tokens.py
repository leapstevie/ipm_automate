from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List

import requests
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session

from app.core.system.db import SessionQipLocal
from app.models.qip.user_model import USER_MODEL, USER_SESSION_MODEL
from config import QIP_BASE_URL 



USER_TYPE_INVESTOR = "investor"
API_QIP = "qip_api"
STATUS_ACTIVE = 1

DEFAULT_QIP_USER_PASSWORD = (os.getenv("DEFAULT_QIP_USER_PASSWORD") or "").strip()


class TokenManager:
    def __init__(self) -> None:
        
        self.access_token: Optional[str] = os.getenv("OVERRIDE_ACCESS_TOKEN") or None
        self.refresh_token: Optional[str] = os.getenv("OVERRIDE_REFRESH_TOKEN") or None
        self.access_token_expire_at: Optional[datetime] = None
        self.refresh_token_expire_at: Optional[datetime] = None
        self.socket_key: Optional[str] = None
        self._threshold = timedelta(minutes=5)

    # ---------------- helpers ----------------

    @staticmethod
    def _parse_dt(val) -> Optional[datetime]:
        if not val:
            return None
        if isinstance(val, datetime):
            return val.replace(tzinfo=timezone.utc) if val.tzinfo is None else val.astimezone(timezone.utc)
        try:
            dt = datetime.fromisoformat(str(val).replace("Z", "+00:00"))
        except Exception:
            return None
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)

    @staticmethod
    def _mk_url(path: str) -> str:
        base = (QIP_BASE_URL or "").rstrip("/")
        return f"{base}{path}" if base.endswith("/api/v1") else f"{base}/api/v1{path}"

    # ---------------- DB: tokens ----------------

    def _load_tokens_from_db(self, user_id: int) -> None:
        """
        Load latest valid investor session tokens from DB for a given user_id.
        """
        session: Session = SessionQipLocal()
        try:
            user_ok = (
                session.query(USER_MODEL.id)
                .filter(USER_MODEL.id == user_id)
                .filter(USER_MODEL.user_type == USER_TYPE_INVESTOR)
                .filter(USER_MODEL.status_id == STATUS_ACTIVE)
                .first()
            )
            if not user_ok:
                raise RuntimeError(f"No active investor found for user_id={user_id}")

            us = (
                session.query(USER_SESSION_MODEL)
                .filter(USER_SESSION_MODEL.user_id == user_id)
                .filter(USER_SESSION_MODEL.api == API_QIP)
                .filter(USER_SESSION_MODEL.access_token.isnot(None))
                .filter(USER_SESSION_MODEL.refresh_token.isnot(None))
                .filter(USER_SESSION_MODEL.refresh_token_expire_at > func.now())
                .order_by(desc(USER_SESSION_MODEL.latest_requested_datetime))
                .first()
            )
            if not us:
                raise RuntimeError(f"No active investor session found in DB for user_id={user_id}")

            self.access_token = us.access_token
            self.refresh_token = us.refresh_token
            self.access_token_expire_at = self._parse_dt(us.access_token_expire_at)
            self.refresh_token_expire_at = self._parse_dt(us.refresh_token_expire_at)

        finally:
            session.close()

    def _get_login_candidates_from_db(self, user_id: int) -> Tuple[str, List[str]]:
        """
        Return (phone_code, [email or phone_number]) for login attempt.
        """
        session: Session = SessionQipLocal()
        try:
            row = (
                session.query(USER_MODEL.email, USER_MODEL.phone_code, USER_MODEL.phone_number)
                .filter(USER_MODEL.id == user_id)
                .filter(USER_MODEL.user_type == USER_TYPE_INVESTOR)
                .filter(USER_MODEL.status_id == STATUS_ACTIVE)
                .first()
            )
            if not row:
                raise RuntimeError(f"No active investor found for login user_id={user_id}")

            phone_code = str(row.phone_code or "855").strip()
            email = (row.email or "").strip()
            phone = str(row.phone_number or "").strip()

            candidates = [v for v in (email, phone) if v]
            if not candidates:
                raise RuntimeError(f"user_id={user_id} missing email/phone_number for login")

            return phone_code, candidates

        finally:
            session.close()

    # ---------------- AUTH ----------------

    def _refresh(self) -> None:
        if not self.refresh_token:
            raise RuntimeError("Cannot refresh: missing refresh_token")

        url = self._mk_url("/auth/refresh")
        res = requests.post(url, json={"refresh_token": self.refresh_token}, headers={"Accept": "*/*"}, timeout=30)
        if res.status_code != 200:
            raise RuntimeError(f"Refresh failed: {res.status_code} {res.text}")

        d = (res.json().get("data") or {})
        self.access_token = d.get("access_token") or self.access_token
        self.refresh_token = d.get("refresh_token") or self.refresh_token
        self.access_token_expire_at = self._parse_dt(d.get("access_token_expire_at")) or self.access_token_expire_at
        self.refresh_token_expire_at = self._parse_dt(d.get("refresh_token_expire_at")) or self.refresh_token_expire_at
        self.socket_key = d.get("socket_key") or self.socket_key

    def _login(self, user_id: int) -> None:
        if not DEFAULT_QIP_USER_PASSWORD:
            raise RuntimeError("DEFAULT_QIP_USER_PASSWORD not set; cannot login")

        phone_code, candidates = self._get_login_candidates_from_db(user_id=user_id)

        url = self._mk_url("/auth/login")
        last_err: Optional[str] = None

        for username in candidates:
            res = requests.post(
                url,
                json={"phone_code": phone_code, "username": username, "password": DEFAULT_QIP_USER_PASSWORD},
                headers={"Accept": "*/*"},
                timeout=30,
            )

            if res.status_code == 200:
                d = (res.json().get("data") or {})
                self.access_token = d.get("access_token")
                self.refresh_token = d.get("refresh_token")
                self.access_token_expire_at = self._parse_dt(d.get("access_token_expire_at"))
                self.refresh_token_expire_at = self._parse_dt(d.get("refresh_token_expire_at"))
                self.socket_key = d.get("socket_key") or self.socket_key

                if not self.access_token:
                    raise RuntimeError("Login OK but access_token missing")
                return

            last_err = f"{res.status_code} {res.text}"

        raise RuntimeError(f"Login failed for user_id={user_id}. Last error: {last_err}")

    # ---------------- PUBLIC ----------------

    def _needs_refresh_by_time(self) -> bool:
        if not self.access_token:
            return True
        if not self.access_token_expire_at:
            return False
        return (self.access_token_expire_at - datetime.now(timezone.utc)) <= self._threshold

    def headers(self, user_id: int | None = None) -> dict:
    # ALWAYS re-read override tokens (important for FastAPI runtime)
        override_access = (os.getenv("OVERRIDE_ACCESS_TOKEN") or "").strip()
        override_refresh = (os.getenv("OVERRIDE_REFRESH_TOKEN") or "").strip()

        if override_access:
            self.access_token = override_access
            if override_refresh:
                self.refresh_token = override_refresh

        if user_id is not None and (not self.access_token or not self.refresh_token):
            self._load_tokens_from_db(user_id=user_id)

        if self._needs_refresh_by_time():
            try:
                self._refresh()
            except Exception:
                # If caller is using override token only, don't attempt DB/password fallback
                if override_access and user_id is None:
                    raise RuntimeError("Invalid/expired OVERRIDE access_token")

                if user_id is None:
                    raise RuntimeError("Unauthorized and no user_id to login with")
                self._login(user_id=user_id)

        if not self.access_token:
            raise RuntimeError("No access_token available")

        return {"Authorization": f"Bearer {self.access_token}", "Accept": "*/*"}


    def on_unauthorized(self, user_id: int | None = None) -> None:
        """
        Force refresh/login after a 401.
        """
        try:
            self._refresh()
        except Exception:
            if user_id is None:
                raise RuntimeError("Unauthorized and no user_id to login with")
            self._login(user_id=user_id)


token_manager = TokenManager()


# ============================================================
# Public query helper
# ============================================================

def list_investor_accounts(search: str | None = None, limit: int = 20, offset: int = 0):
    session: Session = SessionQipLocal()
    try:
        latest_sq = (
            session.query(
                USER_SESSION_MODEL.user_id.label("user_id"),
                func.max(USER_SESSION_MODEL.latest_requested_datetime).label("latest_requested_datetime"),
            )
            .filter(USER_SESSION_MODEL.api == API_QIP)
            .filter(USER_SESSION_MODEL.access_token.isnot(None))
            .filter(USER_SESSION_MODEL.refresh_token.isnot(None))
            .filter(USER_SESSION_MODEL.access_token_expire_at.isnot(None))
            .filter(USER_SESSION_MODEL.refresh_token_expire_at.isnot(None))
            .filter(USER_SESSION_MODEL.refresh_token_expire_at > func.now())
            .group_by(USER_SESSION_MODEL.user_id)
            .subquery()
        )

        q = (
            session.query(
                USER_MODEL.id,
                USER_MODEL.firstname,
                USER_MODEL.lastname,
                USER_MODEL.email,
                USER_MODEL.phone_code,
                USER_MODEL.phone_number,
            )
            .join(latest_sq, latest_sq.c.user_id == USER_MODEL.id)
            .filter(USER_MODEL.user_type == USER_TYPE_INVESTOR)
            .filter(USER_MODEL.status_id == STATUS_ACTIVE)
        )

        if search:
            s = f"%{search.strip()}%"
            q = q.filter(
                or_(
                    USER_MODEL.firstname.ilike(s),
                    USER_MODEL.lastname.ilike(s),
                    USER_MODEL.email.ilike(s),
                    USER_MODEL.phone_number.ilike(s),
                )
            )

        q = q.order_by(USER_MODEL.id.desc()).offset(max(offset, 0)).limit(max(limit, 1))
        rows = q.all()
        return [dict(r._mapping) for r in rows]

    finally:
        session.close()
