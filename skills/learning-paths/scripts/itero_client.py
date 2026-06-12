# Last Edited: 2026-06-11
"""Itero API HTTP wrapper, parameterized by base_url.

Used by the learning-paths skill (practice + tenant APIs) and adapted from
the scorecards skill's scorecard_client.py (practice API).

Auth resolution:
  - tenant=None (default): reads ITERO_API_KEY from .env
  - tenant="<NAME>":       reads ITERO_API_KEY_<NAME> from .env
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import requests
from dotenv import load_dotenv

PRACTICE_BASE = "https://iteropracticeapi.azurewebsites.net"
TENANT_BASE = "https://iterotenantapi.azurewebsites.net"


class Client:
    """HTTP wrapper with dry-run support. Prints every call. Aborts on non-2xx."""

    def __init__(self, base_url: str, tenant: str | None = None, dry_run: bool = True) -> None:
        load_dotenv()
        env_var = f"ITERO_API_KEY_{tenant.upper()}" if tenant else "ITERO_API_KEY"
        api_key = os.getenv(env_var)
        if not api_key:
            raise SystemExit(f"missing env var {env_var} — add it to .env and retry")
        self.base_url = base_url.rstrip("/")
        self.tenant = tenant.upper() if tenant else None
        self.dry_run = dry_run
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _url(self, path: str) -> str:
        return path if path.startswith("http") else f"{self.base_url}{path}"

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = self._url(path)
        print(f"\n{method} {url}")
        if "json" in kwargs:
            print(f"  payload: {json.dumps(kwargs['json'], indent=2, ensure_ascii=False)}")
        if self.dry_run and method in ("POST", "PUT", "DELETE"):
            print("  [DRY-RUN] skipping write")
            if method == "POST":
                stub = hash(url + json.dumps(kwargs.get("json", {}), sort_keys=True)) & 0xFFFF
                return {"id": f"DRY-RUN-{stub}"}
            return {}
        r = requests.request(method, url, headers=self.headers, timeout=30, **kwargs)
        print(f"  -> {r.status_code}")
        if not r.ok:
            print(f"  body: {r.text[:800]}", file=sys.stderr)
            raise SystemExit(f"{method} {url} failed")
        if not r.text:
            return {}
        try:
            return r.json()
        except ValueError:
            return {}

    def get(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params)

    def post(self, path: str, payload: dict) -> Any:
        return self._request("POST", path, json=payload)

    def put(self, path: str, payload: dict) -> Any:
        return self._request("PUT", path, json=payload)

    def delete(self, path: str) -> Any:
        return self._request("DELETE", path)


def unwrap(body: Any) -> list:
    """Catalogs return as a bare list or as {data: [...]} or {items: [...]}."""
    if isinstance(body, list):
        return body
    if isinstance(body, dict):
        data = body.get("data")
        if data is not None:
            return data
        items = body.get("items")
        if items is not None:
            return items
    return []


def pick_id(obj: Any) -> Any:
    """Returns obj['id'] or obj['Id']; None for non-dicts or missing keys."""
    if not isinstance(obj, dict):
        return None
    return obj.get("id") or obj.get("Id")
