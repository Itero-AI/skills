#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Fetch and normalize Itero's public OpenAPI specifications."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GATEWAY_BASE_URL = "https://iterogatewayapi.azurewebsites.net/swagger/docs/public"
TENANT_API_SPEC_URL = (
    "https://iterotenantapi.azurewebsites.net/swagger/public/swagger.json"
)
COMPONENT_REF_PREFIX = "#/components/schemas/"


@dataclass(frozen=True)
class SpecSource:
    """Describe one upstream document and the paths kept from it."""

    url: str
    path_prefixes: tuple[str, ...] | None = None


SPEC_SOURCES = {
    "practice.json": SpecSource(f"{GATEWAY_BASE_URL}/practice"),
    "talk-track.json": SpecSource(f"{GATEWAY_BASE_URL}/talk-track"),
    "tenant.json": SpecSource(f"{GATEWAY_BASE_URL}/tenant"),
    # The usage endpoints are not published through the gateway aggregator, so this
    # snapshot is narrowed to them from the tenant service's own document. Every
    # other tenant path is already covered by tenant.json above.
    "usage.json": SpecSource(TENANT_API_SPEC_URL, ("/api/public/v1/usage",)),
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


def collect_referenced_components(
    node: Any, schemas: Mapping[str, Any], seen: set[str]
) -> set[str]:
    """Walk one subtree and record every component schema it reaches."""
    if isinstance(node, dict):
        reference = node.get("$ref")
        if isinstance(reference, str) and reference.startswith(COMPONENT_REF_PREFIX):
            name = reference[len(COMPONENT_REF_PREFIX) :]
            if name not in seen:
                seen.add(name)
                collect_referenced_components(schemas.get(name), schemas, seen)
        for value in node.values():
            collect_referenced_components(value, schemas, seen)
    elif isinstance(node, list):
        for item in node:
            collect_referenced_components(item, schemas, seen)
    return seen


def narrow_spec(
    filename: str, document: dict[str, Any], prefixes: tuple[str, ...]
) -> dict[str, Any]:
    """Keep only the named paths and the component schemas they reach."""
    paths = {
        path: item
        for path, item in document["paths"].items()
        if path.startswith(prefixes)
    }
    if not paths:
        raise SpecFetchError(
            f"{filename}: upstream document has no path starting with "
            + ", ".join(prefixes)
        )

    schemas = document["components"]["schemas"]
    reachable = collect_referenced_components(paths, schemas, set())
    missing = sorted(reachable - set(schemas))
    if missing:
        raise SpecFetchError(
            f"{filename}: upstream document references undefined schema(s): "
            + ", ".join(missing)
        )

    narrowed = dict(document)
    narrowed["paths"] = paths
    components = dict(document["components"])
    components["schemas"] = {name: schemas[name] for name in sorted(reachable)}
    narrowed["components"] = components
    return narrowed


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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the optional snapshot subset selection."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        choices=sorted(SPEC_SOURCES),
        metavar="SNAPSHOT",
        help=(
            "refresh only this snapshot; repeatable. Use it when one upstream "
            "document is unavailable and the others must still be refreshed. "
            f"Choices: {', '.join(sorted(SPEC_SOURCES))}."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Fetch the selected specifications before replacing any committed snapshot."""
    arguments = parse_args(argv)
    selected = dict.fromkeys(arguments.only) if arguments.only else SPEC_SOURCES

    try:
        documents = {}
        for filename in selected:
            source = SPEC_SOURCES[filename]
            document = fetch_spec(filename, source.url)
            if source.path_prefixes is not None:
                document = narrow_spec(filename, document, source.path_prefixes)
            documents[filename] = document
        replace_specs(documents)
    except SpecFetchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for filename in documents:
        print(f"updated {OUTPUT_DIR / filename}")
    skipped = sorted(set(SPEC_SOURCES) - set(documents))
    if skipped:
        print(f"left unchanged: {', '.join(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
