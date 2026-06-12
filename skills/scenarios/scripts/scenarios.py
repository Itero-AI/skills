#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.28",
#     "python-dotenv>=1.0",
# ]
# ///
# Last Edited: 2026-06-11
"""Itero practice-scenarios skill — CLI.

All write subcommands are dry-run by default. Pass --live to execute.
Pass --tenant NAME to use ITERO_API_KEY_NAME; omit for bare ITERO_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from itero_client import Client, TALK_TRACK_BASE, unwrap, pick_id

PRACTICE_BASE = "https://iteropracticeapi.azurewebsites.net"

SCENARIO_PATH = "/api/public/v1/practice-scenario"
PERSONA_PATH = "/api/public/v1/persona"
CALL_TYPES_PATH = "/api/public/v1/practice-scenario/call-types"
COMM_STYLES_PATH = "/api/public/v1/practice-scenario/communication-styles"
SCORECARD_PATH = "/api/public/v1/scorecard"


# ---------------------------------------------------------------------------
# Catalogs (cached per script invocation, not persisted)
#
# Catalog calls (personas, scorecards, call types, comm styles) can return
# inconsistent data across consecutive calls against the same API key — likely
# an Itero-side caching/routing quirk. Caching here ensures every scenario in
# a batch sees the same catalog snapshot, so name resolution is at least
# internally consistent within one invocation. If you don't trust name
# resolution, use raw IDs in the plan (personaId, scorecardTemplateId,
# practiceScenarioCallTypeId, practiceScenarioCommunicationStyleId) — they
# pass through without any catalog fetch.
# ---------------------------------------------------------------------------

_CATALOG_CACHE: dict[str, list[dict]] = {}


def _cached(client: Client, path: str, cache_key: str, host: str | None = None) -> list[dict]:
    full_key = f"{client.tenant or 'DEFAULT'}::{cache_key}"
    if full_key in _CATALOG_CACHE:
        return _CATALOG_CACHE[full_key]
    if host:
        api_key = client.headers["X-API-Key"]
        r = requests.get(
            f"{host}{path}",
            headers={"X-API-Key": api_key, "Accept": "application/json"},
            timeout=30,
        )
        # Failed or non-JSON responses are NOT cached — a transient error
        # memoized as [] would blank the catalog for every later name
        # resolution in the same batch.
        if not r.ok:
            print(f"  body: {r.text[:800]}", file=sys.stderr)
            raise SystemExit(f"GET {host}{path} failed with status {r.status_code}")
        if not r.text:
            return []
        try:
            items = unwrap(r.json())
        except ValueError:
            return []
    else:
        items = unwrap(client.get(path))
    _CATALOG_CACHE[full_key] = items
    return items


def _list_personas(client: Client) -> list[dict]:
    return _cached(client, PERSONA_PATH, "personas")


def _list_call_types(client: Client) -> list[dict]:
    return _cached(client, CALL_TYPES_PATH, "call_types")


def _list_comm_styles(client: Client) -> list[dict]:
    return _cached(client, COMM_STYLES_PATH, "comm_styles")


def _list_scenarios(client: Client) -> list[dict]:
    # Not cached — scenarios change during a script run (create / delete).
    return unwrap(client.get(SCENARIO_PATH))


def _list_scorecards(client: Client) -> list[dict]:
    """Scorecards live on the Practice API host, not the talk-track host."""
    return _cached(client, SCORECARD_PATH, "scorecards", host=PRACTICE_BASE)


def _name_match(items: list[dict], wanted: str, name_keys=("name", "Name")) -> dict | None:
    """Case-insensitive name match against a catalog list."""
    w = wanted.strip().lower()
    for item in items:
        for k in name_keys:
            v = item.get(k)
            if isinstance(v, str) and v.strip().lower() == w:
                return item
    return None


# ---------------------------------------------------------------------------
# Resolution: turn names into IDs (with raw-ID passthrough)
# ---------------------------------------------------------------------------

_ID_HINT = (
    "If catalog lookups feel unreliable on this tenant, pass raw IDs in the plan "
    "instead — personaId, scorecardTemplateId, practiceScenarioCallTypeId, "
    "practiceScenarioCommunicationStyleId all pass through without a catalog fetch."
)


def _resolve_persona(client: Client, scenario: dict) -> int:
    if "personaId" in scenario:
        return int(scenario["personaId"])
    name = scenario.get("personaName")
    if not name:
        raise SystemExit("scenario must include personaId or personaName")
    personas = _list_personas(client)
    match = _name_match(personas, name)
    if not match:
        names = ", ".join(repr(p.get("name")) for p in personas)
        raise SystemExit(
            f"persona name {name!r} not found in {len(personas)} catalog item(s). "
            f"Available: {names or 'none'}\n\n{_ID_HINT}"
        )
    return int(pick_id(match))


def _resolve_call_type(client: Client, scenario: dict) -> int:
    if "practiceScenarioCallTypeId" in scenario:
        return int(scenario["practiceScenarioCallTypeId"])
    name = scenario.get("callType")
    if not name:
        raise SystemExit("scenario must include practiceScenarioCallTypeId or callType")
    cats = _list_call_types(client)
    match = _name_match(cats, name)
    if not match:
        names = ", ".join(repr(c.get("name")) for c in cats)
        raise SystemExit(
            f"callType {name!r} not found in {len(cats)} catalog item(s). "
            f"Available: {names or 'none'}\n\n{_ID_HINT}"
        )
    return int(pick_id(match))


def _resolve_comm_style(client: Client, scenario: dict) -> int:
    if "practiceScenarioCommunicationStyleId" in scenario:
        return int(scenario["practiceScenarioCommunicationStyleId"])
    name = scenario.get("communicationStyle")
    if not name:
        raise SystemExit("scenario must include practiceScenarioCommunicationStyleId or communicationStyle")
    styles = _list_comm_styles(client)
    match = _name_match(styles, name)
    if not match:
        names = ", ".join(repr(s.get("name")) for s in styles)
        raise SystemExit(
            f"communicationStyle {name!r} not found in {len(styles)} catalog item(s). "
            f"Available: {names or 'none'}\n\n{_ID_HINT}"
        )
    return int(pick_id(match))


def _resolve_scorecard(client: Client, scenario: dict) -> int | None:
    if "scorecardTemplateId" in scenario:
        return int(scenario["scorecardTemplateId"])
    name = scenario.get("scorecardName")
    if not name:
        return None
    cards = _list_scorecards(client)
    match = _name_match(cards, name)
    if not match:
        names = ", ".join(repr(c.get("name")) for c in cards)
        raise SystemExit(
            f"scorecardName {name!r} not found in {len(cards)} catalog item(s). "
            f"Available: {names or 'none'}\n\n{_ID_HINT}"
        )
    return int(pick_id(match))


# ---------------------------------------------------------------------------
# Subcommand: list / fetch
# ---------------------------------------------------------------------------

def cmd_list(client: Client, args: argparse.Namespace) -> None:
    scenarios = _list_scenarios(client)
    if not scenarios:
        print("No scenarios found on this tenant.")
        return
    print(f"\nScenarios ({len(scenarios)}):")
    for s in scenarios:
        sid = pick_id(s)
        name = s.get("practiceScenarioName") or "<unnamed>"
        pid = s.get("personaId") or "?"
        ctid = s.get("practiceScenarioCallTypeId") or "?"
        sct = s.get("scorecardTemplateId") or "—"
        stype = s.get("practiceScenarioType")
        print(f"  id={sid:<6}  name={name!r}  personaId={pid}  callTypeId={ctid}  scorecardTemplateId={sct}  type={stype}")


def cmd_fetch(client: Client, args: argparse.Namespace) -> None:
    scenarios = _list_scenarios(client)
    target = next((s for s in scenarios if str(pick_id(s)) == str(args.id)), None)
    if not target:
        names = ", ".join(f"id={pick_id(s)} name={s.get('practiceScenarioName')!r}" for s in scenarios)
        raise SystemExit(f"scenario id={args.id} not found. Available: {names or 'none'}")
    print(json.dumps(target, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Subcommand: catalog
# ---------------------------------------------------------------------------

def cmd_call_types(client: Client, args: argparse.Namespace) -> None:
    cats = _list_call_types(client)
    print(f"\nCall types ({len(cats)}):")
    for c in cats:
        cid = pick_id(c)
        name = c.get("name") or "<unnamed>"
        desc = c.get("description") or ""
        print(f"  id={cid:<4}  name={name!r}  desc={desc}")


def cmd_comm_styles(client: Client, args: argparse.Namespace) -> None:
    styles = _list_comm_styles(client)
    print(f"\nCommunication styles ({len(styles)}):")
    for s in styles:
        sid = pick_id(s)
        name = s.get("name") or "<unnamed>"
        desc = s.get("description") or ""
        print(f"  id={sid:<4}  name={name!r}  desc={desc}")


# ---------------------------------------------------------------------------
# Subcommand: create (single object OR array, with optional defaults block)
# ---------------------------------------------------------------------------

REQUIRED_TOP_LEVEL = {
    "practiceScenarioName",
    "practiceScenarioDescription",
    "practiceScenarioType",
}


def _normalize_plan(plan: dict | list) -> tuple[dict, list[dict]]:
    """Returns (defaults, scenarios). Accepts:
      - bare dict (single scenario)
      - {"scenarios": [...]} (with optional "defaults": {...})
      - bare list of scenarios
    """
    if isinstance(plan, list):
        return {}, plan
    if isinstance(plan, dict) and "scenarios" in plan and isinstance(plan["scenarios"], list):
        return plan.get("defaults") or {}, plan["scenarios"]
    if isinstance(plan, dict):
        # Single scenario
        return {}, [plan]
    raise SystemExit("plan must be a dict, a list, or {'defaults': {...}, 'scenarios': [...]}")


def _merge_defaults(defaults: dict, scenario: dict) -> dict:
    merged = dict(defaults)
    merged.update(scenario)
    return merged


def _validate_scenario(scenario: dict) -> None:
    missing = sorted(REQUIRED_TOP_LEVEL - scenario.keys())
    if missing:
        raise SystemExit(f"missing required field(s): {', '.join(missing)}")
    stype = scenario["practiceScenarioType"]
    if stype not in (0, 1, 2, 3):
        raise SystemExit(f"practiceScenarioType must be 0/1/2/3; got {stype!r}")
    if stype == 2:
        if not scenario.get("transcript"):
            raise SystemExit("LiveCallSimulation (type=2) requires non-empty 'transcript'")
        if scenario.get("keyBehaviorsOpinions"):
            raise SystemExit("LiveCallSimulation (type=2) must leave keyBehaviorsOpinions null/absent")
    else:
        if not scenario.get("keyBehaviorsOpinions"):
            raise SystemExit(f"practiceScenarioType={stype} requires 'keyBehaviorsOpinions'")


def _build_payload(client: Client, raw: dict) -> dict:
    persona_id = _resolve_persona(client, raw)
    call_type_id = _resolve_call_type(client, raw)
    comm_style_id = _resolve_comm_style(client, raw)
    scorecard_id = _resolve_scorecard(client, raw)

    payload: dict = {
        "personaId": persona_id,
        "practiceScenarioName": raw["practiceScenarioName"],
        "practiceScenarioDescription": raw["practiceScenarioDescription"],
        "practiceScenarioCallTypeId": call_type_id,
        "practiceScenarioCommunicationStyleId": comm_style_id,
        "practiceScenarioType": raw["practiceScenarioType"],
        "omitFromScoring": raw.get("omitFromScoring", False),
        "dialogueStartSetting": raw.get("dialogueStartSetting", 0),
    }

    for opt in (
        "personaBotName",
        "personaCompany",
        "personaTitle",
        "endCallFunctionExpression",
        "starterLine",
        "activityHistories",
        "internalSystems",
        "keyBehaviorsOpinions",
        "transcript",
    ):
        if opt in raw:
            payload[opt] = raw[opt]

    if scorecard_id is not None:
        payload["scorecardTemplateId"] = scorecard_id

    return payload


def cmd_create(client: Client, args: argparse.Namespace) -> None:
    plan_path = Path(args.plan)
    if not plan_path.exists():
        raise SystemExit(f"plan file not found: {plan_path}")
    plan = json.loads(plan_path.read_text())
    defaults, scenarios = _normalize_plan(plan)

    # Validate all upfront so a bad scenario at index 5 doesn't half-create
    merged_list: list[dict] = []
    for i, s in enumerate(scenarios):
        m = _merge_defaults(defaults, s)
        try:
            _validate_scenario(m)
        except SystemExit as e:
            raise SystemExit(f"scenario index {i}: {e}")
        merged_list.append(m)

    print(f"\nCreating {len(merged_list)} scenario(s)...")
    created_ids: list = []
    for i, m in enumerate(merged_list):
        payload = _build_payload(client, m)
        created = client.post(SCENARIO_PATH, payload)
        sid = pick_id(created)
        created_ids.append(sid)
        print(f"  [{i}] Created scenario: id={sid}  name={m['practiceScenarioName']!r}")

    print(f"\nDone: {len(created_ids)} scenario(s) created. IDs: {created_ids}")


# ---------------------------------------------------------------------------
# Subcommand: update
# ---------------------------------------------------------------------------

def cmd_update(client: Client, args: argparse.Namespace) -> None:
    payload = json.loads(args.json)
    payload["id"] = int(args.id)
    client.put(SCENARIO_PATH, payload)
    print(f"\nUpdated scenario id={args.id}")


# ---------------------------------------------------------------------------
# Subcommand: attach-scorecard
# ---------------------------------------------------------------------------

def cmd_attach_scorecard(client: Client, args: argparse.Namespace) -> None:
    scenarios = _list_scenarios(client)
    target = next((s for s in scenarios if str(pick_id(s)) == str(args.scenario_id)), None)
    if not target:
        raise SystemExit(f"scenario id={args.scenario_id} not found")
    target = dict(target)
    target["scorecardTemplateId"] = int(args.template_id)
    target["id"] = int(args.scenario_id)
    client.put(SCENARIO_PATH, target)
    print(f"\nAttached scorecardTemplateId={args.template_id} to scenario id={args.scenario_id}")


# ---------------------------------------------------------------------------
# Subcommand: delete
# ---------------------------------------------------------------------------

def cmd_delete(client: Client, args: argparse.Namespace) -> None:
    client.delete(f"{SCENARIO_PATH}/{args.id}")
    print(f"\nDeleted scenario id={args.id}")


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tenant", default=None)
    common.add_argument("--live", action="store_true")

    p = argparse.ArgumentParser(
        prog="scenarios.py",
        description="Itero practice scenarios CRUD — list, fetch, catalogs, create, update, attach-scorecard, delete.",
        parents=[common],
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", parents=[common])

    fetch_p = sub.add_parser("fetch", parents=[common])
    fetch_p.add_argument("id")

    sub.add_parser("call-types", parents=[common])
    sub.add_parser("communication-styles", parents=[common])

    create_p = sub.add_parser("create", parents=[common])
    create_p.add_argument("plan")

    update_p = sub.add_parser("update", parents=[common])
    update_p.add_argument("id")
    update_p.add_argument("json")

    attach_p = sub.add_parser("attach-scorecard", parents=[common])
    attach_p.add_argument("scenario_id")
    attach_p.add_argument("template_id")

    delete_p = sub.add_parser("delete", parents=[common])
    delete_p.add_argument("id")

    return p


def main() -> None:
    load_dotenv()
    args = build_parser().parse_args()
    client = Client(base_url=TALK_TRACK_BASE, tenant=args.tenant, dry_run=not args.live)
    dispatch = {
        "list": cmd_list,
        "fetch": cmd_fetch,
        "call-types": cmd_call_types,
        "communication-styles": cmd_comm_styles,
        "create": cmd_create,
        "update": cmd_update,
        "attach-scorecard": cmd_attach_scorecard,
        "delete": cmd_delete,
    }
    dispatch[args.command](client, args)


if __name__ == "__main__":
    main()
