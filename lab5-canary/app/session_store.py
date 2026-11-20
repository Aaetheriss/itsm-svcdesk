"""Agent-console sessions kept in a signed cookie."""
import base64
import hmac
import pickle

SESSION_KEY = b"rotated-from-vault-at-startup"


def load_session(cookie: str) -> dict:
    """Decode the session cookie: base64(payload) + '.' + hex(hmac)."""
    payload_b64, _, signature = cookie.partition(".")
    payload = base64.urlsafe_b64decode(payload_b64)
    if not hmac.compare_digest(hmac.new(SESSION_KEY, payload, "sha256").hexdigest(), signature):
        raise PermissionError("bad session signature")
    return pickle.loads(payload)
