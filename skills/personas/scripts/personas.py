#!/usr/bin/env python3
# Last Edited: 2026-04-27
"""Itero personas skill — CLI.

All write subcommands are dry-run by default. Pass --live to execute.
Pass --tenant NAME to use ITERO_API_KEY_NAME; omit for bare ITERO_API_KEY.

Personas are behavioral archetypes; specific individuals belong in scenario keyBehaviorsOpinions.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from itero_client import Client, TALK_TRACK_BASE, unwrap, pick_id

PERSONA_PATH = "/api/public/v1/persona"
VOICES_PATH = "/api/public/v1/persona/voices"


def _list_personas(client: Client) -> list[dict]:
    return unwrap(client.get(PERSONA_PATH))


def cmd_list(client: Client, args: argparse.Namespace) -> None:
    personas = _list_personas(client)
    if not personas:
        print("No personas found on this tenant.")
        return
    print(f"\nPersonas ({len(personas)}):")
    for p in personas:
        pid = pick_id(p)
        ptype = p.get("personaType")
        ptype_label = "Enterprise" if ptype == 0 else ("Consumer" if ptype == 1 else f"?({ptype})")
        name = p.get("name") or "<unnamed>"
        bot = p.get("botName") or ""
        title = p.get("title") or ""
        company = p.get("companyName") or ""
        print(f"  id={pid:<6}  type={ptype_label:<10}  name={name!r}  botName={bot!r}  title={title!r}  company={company!r}")


def cmd_fetch(client: Client, args: argparse.Namespace) -> None:
    # GET /persona/{id} returns 405; list and filter client-side.
    personas = _list_personas(client)
    target = next((p for p in personas if str(pick_id(p)) == str(args.id)), None)
    if not target:
        names = ", ".join(f"id={pick_id(p)} name={p.get('name')!r}" for p in personas)
        raise SystemExit(f"persona id={args.id} not found. Available: {names or 'none'}")
    print(json.dumps(target, indent=2, ensure_ascii=False))


def cmd_voices(client: Client, args: argparse.Namespace) -> None:
    voices = unwrap(client.get(VOICES_PATH))
    if not voices:
        print("No voices returned.")
        return
    print(f"\nVoices ({len(voices)}):")
    for v in voices:
        if isinstance(v, dict):
            vid = v.get("voiceId") or v.get("id") or v.get("Id") or "?"
            name = v.get("name") or v.get("displayName") or ""
            gender = v.get("gender") or ""
            lang = v.get("language") or v.get("locale") or ""
            print(f"  voiceId={vid!r:<40}  name={name!r}  gender={gender}  language={lang}")
        else:
            print(f"  {v}")


REQUIRED_FIELDS_ANY = {"personaType", "name", "botName", "voiceId", "gender", "language"}
REQUIRED_FIELDS_ENT = REQUIRED_FIELDS_ANY | {"title", "companyName"}
REQUIRED_FIELDS_CONS = REQUIRED_FIELDS_ANY | {"practiceScenarioCommunicationStyleId"}


def _validate_create_payload(payload: dict) -> None:
    pt = payload.get("personaType")
    if pt not in (0, 1):
        raise SystemExit(f"personaType must be 0 (Enterprise) or 1 (Consumer); got {pt!r}")
    required = REQUIRED_FIELDS_ENT if pt == 0 else REQUIRED_FIELDS_CONS
    missing = sorted(required - payload.keys())
    if missing:
        raise SystemExit(f"missing required field(s): {', '.join(missing)}")


def cmd_create(client: Client, args: argparse.Namespace) -> None:
    plan_path = Path(args.plan)
    if not plan_path.exists():
        raise SystemExit(f"plan file not found: {plan_path}")
    plan = json.loads(plan_path.read_text())
    _validate_create_payload(plan)
    created = client.post(PERSONA_PATH, plan)
    pid = pick_id(created)
    print(f"\nCreated persona: id={pid}  name={plan.get('name')!r}  botName={plan.get('botName')!r}")


def cmd_update(client: Client, args: argparse.Namespace) -> None:
    payload = json.loads(args.json)
    payload["id"] = int(args.id)
    # PUT /persona (NOT /persona/{id}); id goes in the body. Path-with-id returns 405.
    client.put(PERSONA_PATH, payload)
    print(f"\nUpdated persona id={args.id}")


def cmd_delete(client: Client, args: argparse.Namespace) -> None:
    client.delete(f"{PERSONA_PATH}/{args.id}")
    print(f"\nDeleted persona id={args.id}")


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tenant", default=None)
    common.add_argument("--live", action="store_true")

    p = argparse.ArgumentParser(
        prog="personas.py",
        description="Itero personas CRUD — list, fetch, voices, create, update, delete.",
        parents=[common],
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", parents=[common])

    fetch_p = sub.add_parser("fetch", parents=[common])
    fetch_p.add_argument("id")

    sub.add_parser("voices", parents=[common])

    create_p = sub.add_parser("create", parents=[common])
    create_p.add_argument("plan")

    update_p = sub.add_parser("update", parents=[common])
    update_p.add_argument("id")
    update_p.add_argument("json")

    delete_p = sub.add_parser("delete", parents=[common])
    delete_p.add_argument("id")

    return p


def main() -> None:
    args = build_parser().parse_args()
    client = Client(base_url=TALK_TRACK_BASE, tenant=args.tenant, dry_run=not args.live)
    dispatch = {
        "list": cmd_list,
        "fetch": cmd_fetch,
        "voices": cmd_voices,
        "create": cmd_create,
        "update": cmd_update,
        "delete": cmd_delete,
    }
    dispatch[args.command](client, args)


if __name__ == "__main__":
    main()
