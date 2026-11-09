"""Best-effort RPC analytics using the project's public publishable key."""

import logging
from urllib.parse import urlsplit
from uuid import UUID, NAMESPACE_URL, uuid4, uuid5

import requests
import streamlit as st


LOGGER = logging.getLogger(__name__)
REQUEST_TIMEOUT = (1, 2)  # connect, read; no automatic retries
EVENT_TYPES = frozenset({
    "page_view", "price_open", "price_download", "signup_click",
    "kakao_click", "like", "share",
})
COUNT_KEYS = ("today_visitors", "total_visitors", "likes", "shares")
SUPABASE_URL = "https://zhkxkzsyvpfghafmsytr.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_c0Q5q9n73VZogN9XRXpDKA_BT0ynrD5"


def _get_config():
    try:
        try:
            config = st.secrets.get("analytics", {})
        except FileNotFoundError:
            config = {}
        if config.get("enabled", True) is not True:
            return None
        url = str(config.get("supabase_url", SUPABASE_URL)).strip().rstrip("/")
        key = str(config.get("supabase_publishable_key", SUPABASE_PUBLISHABLE_KEY)).strip()
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https" or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path or not key.startswith("sb_publishable_")
        ):
            LOGGER.warning("[ANALYTICS] configuration unavailable or invalid")
            return None
        return url, key
    except Exception as error:
        # Avoid logging configuration values or response bodies.
        LOGGER.warning("[ANALYTICS] configuration unavailable error_type=%s", type(error).__name__)
        return None


def is_enabled():
    """True only when analytics is explicitly enabled and configured."""
    return _get_config() is not None


def record_event(event_type, session_id, *, event_id=None,
                 utm_source=None, utm_medium=None, utm_content=None, properties=None):
    """Return True when the RPC accepts the event, including duplicates.

    page_view/like have stable IDs so an uncertain response can be retried
    without changing the original timestamp or inflating the count. The DB
    returns False for a duplicate; that is a successful, idempotent outcome.
    """
    try:
        config = _get_config()
        if config is None:
            return False
        if event_type not in EVENT_TYPES:
            raise ValueError("Unsupported event type")
        session_id = str(UUID(str(session_id)))
        if event_type in {"page_view", "like"}:
            event_id = uuid5(NAMESPACE_URL, f"meat-lab:{session_id}:{event_type}")
        else:
            event_id = UUID(str(event_id)) if event_id is not None else uuid4()
        payload = {
            "p_event_id": str(event_id), "p_session_id": session_id, "p_event_type": event_type,
            "p_utm_source": str(utm_source)[:255] if utm_source is not None else None,
            "p_utm_medium": str(utm_medium)[:255] if utm_medium is not None else None,
            "p_utm_content": str(utm_content)[:255] if utm_content is not None else None,
            "p_properties": properties,
        }
        url, key = config
        response = requests.post(
            f"{url}/rest/v1/rpc/record_event",
            headers={"apikey": key},
            json=payload, timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        if type(response.json()) is not bool:
            raise ValueError("Unexpected record_event RPC response")
        return True
    except Exception as error:
        LOGGER.warning("[ANALYTICS] record_event failed error_type=%s", type(error).__name__)
        return False


def get_social_counts():
    """Return the four DB counts, or None when disabled/unavailable."""
    try:
        config = _get_config()
        if config is None:
            return None
        url, key = config
        response = requests.post(
            f"{url}/rest/v1/rpc/get_social_counts",
            headers={"apikey": key}, json={}, timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        rows = response.json()
        # Supabase SQL functions may return a JSON object or a single table row.
        if isinstance(rows, dict):
            row = rows
        elif isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict):
            row = rows[0]
        else:
            raise ValueError("Unexpected count response")
        counts = {name: row[name] for name in COUNT_KEYS}
        if any(type(value) is not int or value < 0 for value in counts.values()):
            raise ValueError("Invalid counts")
        return counts
    except Exception as error:
        LOGGER.warning("[ANALYTICS] get_social_counts failed error_type=%s", type(error).__name__)
        return None
