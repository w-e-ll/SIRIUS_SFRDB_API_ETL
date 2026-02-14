#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import base64
import json
import sys
import os
import logging

import requests

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


logger = logging.getLogger('fetcher_token_manager')
CLIENT_ID = "sirius"
SCOPE = "sf-rdb"

SESSION = requests.Session()
SESSION.trust_env = False
SESSION.headers.update({"Accept": "application/json"})
SESSION.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=5,
            backoff_factor=0.6,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"GET", "POST"}
        )
    )
)


class TokenManager:
    def __init__(self, cfg):
        self.cfg = cfg
        self.token = None
        self.exp_epoch = 0

    def _decode_exp(self, jwt_token):
        try:
            parts = jwt_token.split(".")
            if len(parts) < 2:
                return 0
            pad = "=" * (-len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(parts[1] + pad))
            return int(payload.get("exp", 0))
        except Exception as exc:
            logger.error(f"Decode error {exc}")
            return 0

    def refresh(self):
        CLIENT_SECRET = os.getenv("SFRDB_CLIENT_SECRET", "")
        if not CLIENT_SECRET:
            logger.error("ERROR: SFRDB_CLIENT_SECRET is not set")
            sys.exit(2)

        data = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": SCOPE,
        }

        logger.info("Refreshing SFRDB token…")

        try:
            r = SESSION.post(self.cfg["token_url"], data=data, verify=False, timeout=30)
        except Exception as exc:
            logger.error(f"Could not post token_url for refresh: {exc}")
            raise

        r.raise_for_status()
        tok = r.json()["access_token"]

        self.token = tok
        self.exp_epoch = self._decode_exp(tok)

    def get(self):
        """Return current token, refresh if needed."""
        if self.token is None or (self.exp_epoch and time.time() > self.exp_epoch - 300):
            self.refresh()
        return self.token


def auth_get(tm: TokenManager, url: str, params=None):
    """Wrapper replacing global auth_get from original file."""
    headers = {"Authorization": f"Bearer {tm.get()}"}

    r = SESSION.get(url, headers=headers, params=(params or {}), timeout=90, verify=False)

    if r.status_code == 401:
        tm.refresh()
        headers = {"Authorization": f"Bearer {tm.get()}"}
        r = SESSION.get(url, headers=headers, params=(params or {}), timeout=90, verify=False)

    r.raise_for_status()
    return r
