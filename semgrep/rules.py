# ai-generated: 100% - ChatGPT wrote true-positive and true-negative examples for the two Lab 5 Semgrep rules.
import sqlite3

import httpx


def open_ticket_database(path):
    # ruleid: svcdesk-sqlite-connection-review
    return sqlite3.connect(path, timeout=30)


def already_open_connection(connection):
    # ok: svcdesk-sqlite-connection-review
    return connection.cursor()


async def make_kb_client(timeout, limits):
    # ruleid: svcdesk-httpx-async-client-review
    return httpx.AsyncClient(timeout=timeout, limits=limits)


def make_sync_client(timeout):
    # ok: svcdesk-httpx-async-client-review
    return httpx.Client(timeout=timeout)
