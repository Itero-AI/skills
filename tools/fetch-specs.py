#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Fetch and normalize Itero's public OpenAPI specifications."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://iterogatewayapi.azurewebsites.net/swagger/docs/public"
SPEC_URLS = {
    "practice.json": f"{BASE_URL}/practice",
    "talk-track.json": f"{BASE_URL}/talk-track",
    "tenant.json": f"{BASE_URL}/tenant",
}
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "spec"
REQUEST_TIMEOUT_SECONDS = 30


class SpecFetchError(RuntimeError):
    """Raised when a public specification cannot be fetched or validated."""


def fetch_spec(filename: str, url: str) -> dict[str, Any]:
    """Fetch one OpenAPI document and validate its required top-level shape."""
    request = Request(url, headers={"User-Agent": "itero-skills-spec-fetcher/2.0"})

    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read()
    except HTTPError as exc:
        raise SpecFetchError(
            f"failed to fetch {filename} from {url}: HTTP {exc.code}"
        ) from exc
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise SpecFetchError(
            f"failed to fetch {filename} from {url}: {reason}"
        ) from exc
    except TimeoutError as exc:
        raise SpecFetchError(
            f"timed out after {REQUEST_TIMEOUT_SECONDS}s fetching {filename} from {url}"
        ) from exc

    try:
        document = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SpecFetchError(f"{url} did not return valid UTF-8 JSON") from exc

    if not isinstance(document, dict):
        raise SpecFetchError(f"{url} returned JSON that is not an object")
    if document.get("openapi") != "3.0.1":
        raise SpecFetchError(
            f"{url} returned OpenAPI version {document.get('openapi')!r}; expected '3.0.1'"
        )
    if not isinstance(document.get("paths"), dict):
        raise SpecFetchError(f"{url} returned a document without a paths object")
    components = document.get("components")
    if not isinstance(components, dict) or not isinstance(
        components.get("schemas"), dict
    ):
        raise SpecFetchError(f"{url} returned a document without components.schemas")

    return document


def serialize_spec(document: dict[str, Any]) -> bytes:
    """Return a stable, review-friendly JSON representation."""
    rendered = json.dumps(
        document,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    return f"{rendered}\n".encode()


def replace_specs(documents: dict[str, dict[str, Any]]) -> None:
    """Stage every snapshot, then replace the set with best-effort rollback."""
    staged: dict[Path, Path] = {}
    originals: dict[Path, bytes | None] = {}
    replaced: list[Path] = []

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        for filename, document in documents.items():
            destination = OUTPUT_DIR / filename
            originals[destination] = (
                destination.read_bytes() if destination.exists() else None
            )
            file_descriptor, temporary_name = tempfile.mkstemp(
                dir=OUTPUT_DIR,
                prefix=f".{filename}.",
                suffix=".tmp",
            )
            temporary_path = Path(temporary_name)
            staged[destination] = temporary_path

            with os.fdopen(file_descriptor, "wb") as temporary_file:
                temporary_file.write(serialize_spec(document))
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            temporary_path.chmod(0o644)

        for destination, temporary_path in staged.items():
            os.replace(temporary_path, destination)
            replaced.append(destination)
    except OSError as exc:
        rollback_errors: list[str] = []
        for destination in reversed(replaced):
            try:
                original = originals[destination]
                if original is None:
                    destination.unlink(missing_ok=True)
                    continue
                descriptor, temporary_name = tempfile.mkstemp(
                    dir=destination.parent,
                    prefix=f".{destination.name}.rollback.",
                    suffix=".tmp",
                )
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(original)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary_name, destination)
            except OSError as rollback_exc:
                rollback_errors.append(f"{destination.name}: {rollback_exc}")
        details = f"failed to write snapshots in {OUTPUT_DIR}: {exc}"
        if rollback_errors:
            details += "; rollback also failed for " + "; ".join(rollback_errors)
        raise SpecFetchError(details) from exc
    finally:
        for temporary_path in staged.values():
            temporary_path.unlink(missing_ok=True)


def main() -> int:
    """Fetch all specifications before replacing any committed snapshot."""
    try:
        documents = {
            filename: fetch_spec(filename, url) for filename, url in SPEC_URLS.items()
        }
        replace_specs(documents)
    except SpecFetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for filename in SPEC_URLS:
        print(f"updated {OUTPUT_DIR / filename}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
