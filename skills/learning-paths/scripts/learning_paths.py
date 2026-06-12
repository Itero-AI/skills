#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.28",
#     "python-dotenv>=1.0",
# ]
# ///
"""Itero learning-paths skill — CLI.

Read-only listing of learning paths / certifications plus assign / reassign.
There is NO public API to create, edit, or delete learning paths — that is
Studio-only. Write subcommands are dry-run by default; pass --live to execute.
Pass --tenant NAME to use ITERO_API_KEY_NAME; omit for bare ITERO_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import re

from itero_client import Client, PRACTICE_BASE, TENANT_BASE, unwrap, pick_id

LP_PATH = "/api/public/v1/learning-path"
USERS_PATH = "/api/public/v1/user"
TYPE_LABELS = {0: "Learning Path", 1: "Certification"}


def _normalize_due(due: str) -> str:
    # API requires UTC date-time; future-only. Convert bare YYYY-MM-DD to end-of-day UTC.
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", due):
        return f"{due}T23:59:59Z"
    return due


def cmd_list(client: Client, args: argparse.Namespace) -> None:
    params = {"type": args.type} if args.type is not None else None
    paths = unwrap(client.get(LP_PATH, params=params))
    if not paths:
        print("No learning paths found on this tenant.")
        return
    print(f"\nLearning paths ({len(paths)}):")
    for lp in paths:
        t = TYPE_LABELS.get(lp.get("type"), f"?({lp.get('type')})")
        print(
            f"  id={pick_id(lp):<6} [{t}] {lp.get('title')!r}  "
            f"stages={lp.get('stagesAmount')}  ordered={lp.get('isOrdered')}  "
            f"retriable={lp.get('isRetriable')}"
        )


def cmd_fetch(client: Client, args: argparse.Namespace) -> None:
    details = client.get(f"{LP_PATH}/{args.id}")
    print(json.dumps(details, indent=2, ensure_ascii=False))
    assignments = details.get("assignments") or []
    print(f"\n{len(assignments)} current assignment(s).")


def cmd_users(client: Client, args: argparse.Namespace) -> None:
    """List tenant users with the tenantUserId needed for assignment."""
    tenant_client = Client(TENANT_BASE, tenant=args.tenant, dry_run=True)
    params: dict = {}
    if args.role:
        params["role"] = args.role
    if args.active is not None:
        params["isActive"] = args.active
    users = unwrap(tenant_client.get(USERS_PATH, params=params or None))
    print(f"\nUsers ({len(users)}):  (use tenantUserId for assignments)")
    for u in users:
        print(
            f"  tenantUserId={u.get('tenantUserId'):<6} id={u.get('id'):<6} "
            f"{u.get('role'):<15} active={u.get('isActive')!s:<5} "
            f"{u.get('name')!r} <{u.get('email')}>"
        )


def _assignments_payload(args: argparse.Namespace) -> dict:
    try:
        ids = [int(x) for x in args.user_ids.split(",") if x.strip()]
    except ValueError:
        raise SystemExit(f"--user-ids values must be integers, got: {args.user_ids}")
    if not ids:
        raise SystemExit("--user-ids must contain at least one tenantUserId")
    items = []
    for uid in ids:
        item: dict = {"tenantUserId": uid}
        if args.due:
            item["dueDate"] = _normalize_due(args.due)
        items.append(item)
    return {"assignments": items}


def cmd_assign(client: Client, args: argparse.Namespace) -> None:
    client.post(f"{LP_PATH}/{args.id}/assign", _assignments_payload(args))
    print("Assigned." if not client.dry_run else "(dry-run — pass --live to execute)")


def cmd_reassign(client: Client, args: argparse.Namespace) -> None:
    client.post(f"{LP_PATH}/{args.id}/reassign", _assignments_payload(args))
    print("Reassigned." if not client.dry_run else "(dry-run — pass --live to execute)")


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tenant", default=None)
    common.add_argument("--live", action="store_true")

    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", parents=[common])
    list_p.add_argument("--type", type=int, choices=[0, 1], default=None,
                        help="0=Learning Path, 1=Certification")

    fetch_p = sub.add_parser("fetch", parents=[common])
    fetch_p.add_argument("id", type=int)

    users_p = sub.add_parser("users", parents=[common])
    users_p.add_argument("--role", choices=["Representative", "Manager"], default=None)
    users_p.add_argument("--active", default=None)

    for name in ("assign", "reassign"):
        w = sub.add_parser(name, parents=[common])
        w.add_argument("id", type=int)
        w.add_argument("--user-ids", required=True,
                       help="comma-separated tenantUserId values (from `users`)")
        w.add_argument("--due", default=None,
                       help="due date: YYYY-MM-DD (sent as end-of-day UTC) or full ISO 8601 UTC timestamp; must be in the future")

    return p


def main() -> None:
    args = build_parser().parse_args()
    client = Client(PRACTICE_BASE, tenant=args.tenant, dry_run=not args.live)
    {
        "list": cmd_list,
        "fetch": cmd_fetch,
        "users": cmd_users,
        "assign": cmd_assign,
        "reassign": cmd_reassign,
    }[args.command](client, args)


if __name__ == "__main__":
    main()
