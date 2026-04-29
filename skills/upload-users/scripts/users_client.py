# Last Edited: 2026-04-27
"""Itero Tenant API HTTP wrapper for the upload-users skill.

Self-contained — does not import from execution/itero_app/.
Auth resolution:
  - tenant=None (default): reads ITERO_API_KEY from .env
  - tenant="<NAME>":       reads ITERO_API_KEY_<NAME> from .env

Adds `post_multipart` for the bulk-import-csv endpoint. The shared
`itero_client.py` in execution/itero_app/ is intentionally not extended —
skills are self-contained so the folder can be dropped into any harness.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any

import requests
from dotenv import load_dotenv

TENANT_BASE = "https://iterotenantapi.azurewebsites.net"


class Client:
    """HTTP wrapper with dry-run support. Prints every call. Aborts on non-2xx."""

    def __init__(self, tenant: str | None = None, dry_run: bool = True) -> None:
        load_dotenv()
        env_var = f"ITERO_API_KEY_{tenant.upper()}" if tenant else "ITERO_API_KEY"
        api_key = os.getenv(env_var)
        if not api_key:
            raise SystemExit(f"missing env var {env_var} — add it to .env and retry")
        self.tenant = tenant.upper() if tenant else None
        self.dry_run = dry_run
        self.api_key = api_key

    def _json_headers(self) -> dict:
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _multipart_headers(self) -> dict:
        # requests sets Content-Type with boundary itself when files= is used.
        return {
            "X-API-Key": self.api_key,
            "Accept": "application/json",
        }

    def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        print(f"\n{method} {url}")
        if "json" in kwargs:
            print(f"  payload: {json.dumps(kwargs['json'], indent=2, ensure_ascii=False)}")
        if self.dry_run and method in ("POST", "PUT", "DELETE"):
            print("  [DRY-RUN] skipping write")
            return {} if method != "POST" else {"id": "DRY-RUN"}
        r = requests.request(method, url, headers=self._json_headers(), timeout=30, **kwargs)
        return self._handle_response(method, url, r)

    @staticmethod
    def _handle_response(method: str, url: str, r: requests.Response) -> Any:
        print(f"  -> {r.status_code}")
        if not r.ok:
            print(f"  body: {r.text[:1500]}", file=sys.stderr)
            raise SystemExit(f"{method} {url} failed")
        if not r.text:
            return {}
        try:
            return r.json()
        except ValueError:
            return r.text

    def get(self, url: str, params: dict | None = None) -> Any:
        return self._request("GET", url, params=params)

    def post(self, url: str, payload: dict) -> Any:
        return self._request("POST", url, json=payload)

    def post_multipart(
        self,
        url: str,
        *,
        filename: str,
        content: bytes,
        content_type: str = "text/csv",
        field_name: str = "file",
    ) -> Any:
        """POST a multipart/form-data body with one file field.

        Honors dry_run — prints the file size and field name but does not send.
        """
        print(f"\nPOST {url}")
        print(f"  multipart: {field_name}={filename!r} ({len(content)} bytes, {content_type})")
        if self.dry_run:
            print("  [DRY-RUN] skipping multipart upload")
            return {"dryRun": True, "bytes": len(content)}
        files = {field_name: (filename, content, content_type)}
        r = requests.post(url, headers=self._multipart_headers(), files=files, timeout=60)
        return self._handle_response("POST", url, r)


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
