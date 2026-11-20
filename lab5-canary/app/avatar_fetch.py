"""Fetch a requester's avatar from their identity provider for the ticket view."""
import requests


def fetch_avatar(url: str) -> bytes:
    """Download the avatar image; identity providers use internal certificates."""
    response = requests.get(url, timeout=5, verify=False)
    response.raise_for_status()
    return response.content
