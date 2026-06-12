#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.28",
#     "python-dotenv>=1.0",
# ]
# ///
"""Itero manage-users skill — CLI.

Single-user lifecycle: list, create, update, activate/deactivate, delete.
Bulk CSV import lives in the upload-users skill. Write subcommands are
dry-run by default; pass --live to execute. Pass --tenant NAME to use
ITERO_API_KEY_NAME; omit for bare ITERO_API_KEY.

Note: all /api/public/v1/user endpoints are documented as requiring an Owner-role API key.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from itero_client import Client, TENANT_BASE, unwrap

USER_PATH = "/api/public/v1/user"
GROUPS_PATH = "/api/Public/v1/get-user-groups"  # capital P is intentional

# All four valid roles. Only Representative and Manager consume a billable seat.
VALID_ROLES = ("Representative", "Manager", "Coach", "Owner")


def _list_users(client: Client, role: str | None = None, active=None) -> list[dict]:
    params: dict = {}
    if role:
        params["role"] = role
    if active is not None:
        params["isActive"] = active
    return unwrap(client.get(USER_PATH, params=params or None))


def _print_user(u: dict) -> None:
    groups = ", ".join(g.get("name", "?") for g in (u.get("groups") or []))
    print(
        f"  id={u.get('id'):<6} tenantUserId={u.get('tenantUserId'):<6} "
        f"{u.get('role'):<15} active={u.get('isActive')!s:<5} "
        f"{u.get('name')!r} <{u.get('email')}>  groups=[{groups}]"
    )


def cmd_list(client: Client, args: argparse.Namespace) -> None:
    users = _list_users(client, args.role, args.active)
    print(f"\nUsers ({len(users)}):")
    for u in users:
        _print_user(u)


def cmd_fetch(client: Client, args: argparse.Namespace) -> None:
    users = _list_users(client)
    target = next((u for u in users if str(u.get("id")) == str(args.id)), None)
    if not target:
        raise SystemExit(f"user id={args.id} not found (run `list` to see ids)")
    print(json.dumps(target, indent=2, ensure_ascii=False))


def cmd_list_groups(client: Client, args: argparse.Namespace) -> None:
    groups = unwrap(client.get(GROUPS_PATH))
    print(f"\nUser groups ({len(groups)}):")
    for g in groups:
        # The legacy groups endpoint field naming is inconsistent across the API
        # (other scripts read name/Name); be defensive across all known variants.
        title = g.get("title") or g.get("name") or g.get("Name") or "<unnamed>"
        print(f"  id={g.get('id'):<6} {title!r}")


def cmd_create(client: Client, args: argparse.Namespace) -> None:
    payload = json.loads(Path(args.plan).read_text())
    for field in ("name", "email", "role"):
        if not payload.get(field):
            raise SystemExit(f"missing required field: {field}")
    if payload["role"] not in VALID_ROLES:
        raise SystemExit(f"role must be one of: {', '.join(VALID_ROLES)}")
    if payload.get("isActive", True) and payload["role"] in ("Representative", "Manager"):
        print(
            "INFO: activating a Representative or Manager consumes a billable seat; "
            "may 400 at the seat limit"
        )
    print("INFO: an invitation email will be sent to the user on creation")
    created = client.post(USER_PATH, payload)
    print(f"Created user id={created.get('id')}" if not client.dry_run
          else "(dry-run — pass --live to execute)")


def cmd_update(client: Client, args: argparse.Namespace) -> None:
    payload = json.loads(args.payload)
    payload["id"] = int(args.id)
    for field in ("name", "role"):
        if not payload.get(field):
            raise SystemExit(f"missing required field: {field} (PUT needs the complete object)")
    client.put(USER_PATH, payload)
    print("Updated." if not client.dry_run else "(dry-run — pass --live to execute)")


def _toggle_active(client: Client, user_id: str, active: bool) -> None:
    users = _list_users(client)
    target = next((u for u in users if str(u.get("id")) == str(user_id)), None)
    if not target:
        raise SystemExit(f"user id={user_id} not found")
    payload = {
        "id": target["id"],
        "name": target.get("name"),
        "role": target.get("role"),
        "isActive": active,
        "groups": [g.get("name") for g in (target.get("groups") or [])],
    }
    client.put(USER_PATH, payload)
    state = "activated" if active else "deactivated"
    print(f"{state}." if not client.dry_run else "(dry-run — pass --live to execute)")


def cmd_deactivate(client: Client, args: argparse.Namespace) -> None:
    _toggle_active(client, args.id, False)


def cmd_activate(client: Client, args: argparse.Namespace) -> None:
    _toggle_active(client, args.id, True)


def cmd_delete(client: Client, args: argparse.Namespace) -> None:
    # Wiki leaves three things unconfirmed for live DELETE:
    #   1. Whether the path id is the DTO `id` or `tenantUserId`
    #      (the wiki example suggests tenantUserId while PUT uses DTO id).
    #   2. Whether delete is hard or soft.
    #   3. Whether it frees the seat immediately.
    # Live deletes are therefore refused entirely until platform confirms these semantics.
    # --confirm-email is reserved for when delete semantics are confirmed.
    users = _list_users(client)
    target = next((u for u in users if str(u.get("id")) == str(args.id)), None)
    if not target:
        raise SystemExit(f"user id={args.id} not found (run `list` to see ids)")
    print(f"Target: id={target['id']} {target.get('name')!r} <{target.get('email')}>")
    if not client.dry_run:
        raise SystemExit(
            "refusing live delete: delete semantics are pending platform confirmation "
            "(which id the path takes, hard-vs-soft, seat release) — use deactivate instead."
        )
    # Dry-run preview: note that id semantics are unconfirmed before showing the call.
    print(
        "WARNING: id semantics are unconfirmed (DTO id vs tenantUserId); "
        "do not rely on this path until platform confirms."
    )
    client.delete(f"{USER_PATH}/{args.id}")
    print("(dry-run — pass --live to execute)")


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tenant", default=None)
    common.add_argument("--live", action="store_true")

    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", parents=[common])
    list_p.add_argument("--role", choices=list(VALID_ROLES), default=None)
    list_p.add_argument("--active", default=None)

    fetch_p = sub.add_parser("fetch", parents=[common])
    fetch_p.add_argument("id")

    sub.add_parser("list-groups", parents=[common])

    create_p = sub.add_parser("create", parents=[common])
    create_p.add_argument("plan", help="path to plan.json: {name, email, role, isActive?, groups?}")

    update_p = sub.add_parser("update", parents=[common])
    update_p.add_argument("id")
    update_p.add_argument("payload", help="complete JSON: {name, role, isActive, groups}")

    for name in ("deactivate", "activate"):
        w = sub.add_parser(name, parents=[common])
        w.add_argument("id")

    delete_p = sub.add_parser("delete", parents=[common])
    delete_p.add_argument("id")
    delete_p.add_argument(
        "--confirm-email",
        default=None,
        help=(
            "reserved for when delete semantics are confirmed (which id the path takes, "
            "hard-vs-soft, seat release); live delete is currently refused regardless"
        ),
    )

    return p


def main() -> None:
    args = build_parser().parse_args()
    client = Client(TENANT_BASE, tenant=args.tenant, dry_run=not args.live)
    {
        "list": cmd_list,
        "fetch": cmd_fetch,
        "list-groups": cmd_list_groups,
        "create": cmd_create,
        "update": cmd_update,
        "deactivate": cmd_deactivate,
        "activate": cmd_activate,
        "delete": cmd_delete,
    }[args.command](client, args)


if __name__ == "__main__":
    main()
