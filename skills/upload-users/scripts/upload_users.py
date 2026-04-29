#!/usr/bin/env python3
# Last Edited: 2026-04-27
"""
Itero upload-users skill — CLI.

All write subcommands are dry-run by default. Pass --live on `import` to actually POST.
Pass --tenant NAME to use ITERO_API_KEY_NAME; omit for bare ITERO_API_KEY.

Subcommands:
  inspect <csv>           Parse the CSV, surface validation issues, write the initial plan.
  list-groups             GET /api/Public/v1/get-user-groups on the tenant host.
  list-users              GET /api/Public/v1/get-users on the tenant host.
  suggest-groups          Read plan, propose UserGroup assignments based on signals.
  check-duplicates        Cross-reference plan emails against current tenant users.
  check-seats             Compute seat math against ITERO_TENANT_SEATS_<TENANT> (or skip).
  preview                 Print the final state of the plan with summary counts.
  import [--live]         POST the plan as a CSV to /api/public/v1/user/import-csv.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from users_client import Client, TENANT_BASE, unwrap


VALID_ROLES = {"Manager", "Representative"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DEFAULT_PLAN_PATH = ".tmp/users-import-plan.json"
MAX_CSV_BYTES = 1_048_576  # 1 MB


# ---------------------------------------------------------------------------
# Plan I/O
# ---------------------------------------------------------------------------

def _plan_path(args: argparse.Namespace) -> Path:
    return Path(args.plan or DEFAULT_PLAN_PATH)


def load_plan(args: argparse.Namespace) -> dict:
    path = _plan_path(args)
    if not path.exists():
        raise SystemExit(
            f"plan not found at {path}. Run `inspect <csv>` first to create it."
        )
    return json.loads(path.read_text())


def save_plan(args: argparse.Namespace, plan: dict) -> None:
    path = _plan_path(args)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    print(f"  plan saved -> {path}")


# ---------------------------------------------------------------------------
# CSV parsing + validation
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = ("Name", "Email", "Role")
OPTIONAL_COLUMNS = ("IsActive", "UserGroup")
ALL_COLUMNS = REQUIRED_COLUMNS + OPTIONAL_COLUMNS


def _normalize_header(h: str) -> str:
    """Header matching is case-insensitive on the server. We canonicalize to the documented case."""
    canonical = {c.lower(): c for c in ALL_COLUMNS}
    return canonical.get(h.strip().lower(), h.strip())


def _parse_isactive(raw: str | None) -> tuple[bool | None, str | None]:
    """Return (parsed_bool, error). Blank/missing → (True, None) per the directive default."""
    if raw is None or raw.strip() == "":
        return True, None
    v = raw.strip().lower()
    if v in ("true", "false"):
        return v == "true", None
    return None, f"unrecognized IsActive value {raw!r} (use true or false)"


def parse_csv(path: Path) -> tuple[list[dict], list[dict]]:
    """Return (rows, issues). Each row is a dict with keys matching ALL_COLUMNS where present.

    Issues look like {row: int|None, column: str, value: str, kind: str, message: str}.
    Row 1 is the header; data rows start at 2.
    """
    issues: list[dict] = []
    rows: list[dict] = []

    if not path.exists():
        raise SystemExit(f"CSV not found: {path}")
    if path.suffix.lower() != ".csv":
        raise SystemExit(
            f"file is {path.suffix!r}, not .csv. Save as CSV first "
            "(in Excel: File → Save As → CSV (Comma delimited))."
        )
    size = path.stat().st_size
    if size == 0:
        raise SystemExit(f"file is empty: {path}")
    if size > MAX_CSV_BYTES:
        raise SystemExit(
            f"file is {size} bytes, over the 1 MB import limit. Split into smaller batches."
        )

    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.reader(fh)
        try:
            header = next(reader)
        except StopIteration:
            raise SystemExit(f"file has no rows: {path}")

        canonical = [_normalize_header(h) for h in header]
        present = set(canonical)
        for col in REQUIRED_COLUMNS:
            if col not in present:
                issues.append({
                    "row": None, "column": col, "value": "",
                    "kind": "missing_column",
                    "message": f"required column {col!r} is missing from the header row",
                })

        if any(i["kind"] == "missing_column" for i in issues):
            return rows, issues

        for line_no, raw in enumerate(reader, start=2):
            row: dict[str, Any] = {"_line": line_no}
            cells = list(raw) + [""] * (len(canonical) - len(raw))
            for col_name, cell in zip(canonical, cells):
                if col_name in ALL_COLUMNS:
                    row[col_name] = cell.strip() if isinstance(cell, str) else cell

            issues.extend(_validate_row(row))
            rows.append(row)

    return rows, issues


def _validate_row(row: dict) -> list[dict]:
    line = row["_line"]
    out: list[dict] = []

    name = row.get("Name", "")
    if not name:
        out.append({"row": line, "column": "Name", "value": "", "kind": "missing_value",
                    "message": "Name is required and cannot be blank"})
    elif len(name) > 100:
        out.append({"row": line, "column": "Name", "value": name, "kind": "too_long",
                    "message": f"Name is {len(name)} chars; max is 100"})

    email = row.get("Email", "")
    if not email:
        out.append({"row": line, "column": "Email", "value": "", "kind": "missing_value",
                    "message": "Email is required and cannot be blank"})
    elif not EMAIL_RE.match(email):
        out.append({"row": line, "column": "Email", "value": email, "kind": "bad_email",
                    "message": f"{email!r} is not a valid email address"})
    elif len(email) > 100:
        out.append({"row": line, "column": "Email", "value": email, "kind": "too_long",
                    "message": f"Email is {len(email)} chars; max is 100"})

    role = row.get("Role", "")
    if not role:
        out.append({"row": line, "column": "Role", "value": "", "kind": "missing_value",
                    "message": "Role is required (Manager or Representative)"})
    elif role not in VALID_ROLES:
        out.append({"row": line, "column": "Role", "value": role, "kind": "bad_role",
                    "message": f"{role!r} is not a valid Role. Use Manager or Representative."})

    is_active_raw = row.get("IsActive", None)
    parsed, err = _parse_isactive(is_active_raw)
    row["_isActiveParsed"] = parsed
    if err:
        out.append({"row": line, "column": "IsActive", "value": str(is_active_raw or ""),
                    "kind": "bad_isactive", "message": err})

    return out


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_inspect(client: Client | None, args: argparse.Namespace) -> None:
    csv_path = Path(args.csv).expanduser().resolve()
    rows, issues = parse_csv(csv_path)

    blocking = [i for i in issues if i["kind"] in (
        "missing_column", "missing_value", "bad_email", "bad_role", "too_long", "bad_isactive"
    )]

    print(f"\nFile:      {csv_path}")
    print(f"Rows:      {len(rows)}")
    print(f"Issues:    {len(issues)}")

    if issues:
        by_kind: dict[str, list[dict]] = {}
        for i in issues:
            by_kind.setdefault(i["kind"], []).append(i)
        for kind, items in by_kind.items():
            print(f"\n  [{kind}] {len(items)}:")
            for item in items[:10]:
                row_label = f"row {item['row']}" if item["row"] is not None else "header"
                print(f"    {row_label:>10}: {item['message']}")
            if len(items) > 10:
                print(f"    ... +{len(items) - 10} more")

    sample = rows[:3]
    if sample:
        print("\nFirst rows:")
        for r in sample:
            print(f"  {r['_line']:>3}: Name={r.get('Name','')!r}  Email={r.get('Email','')!r}  "
                  f"Role={r.get('Role','')!r}  IsActive={r.get('_isActiveParsed')}  "
                  f"UserGroup={r.get('UserGroup','')!r}")

    plan_rows = [_row_to_plan(r) for r in rows]
    plan = {
        "source_csv": str(csv_path),
        "tenant": (client.tenant if client else None) or args.tenant,
        "rows": plan_rows,
        "groups": _summarize_groups(plan_rows, existing_groups=set()),
        "validation": {
            "issues": issues,
            "duplicates_dropped": [],
            "rows_deactivated_for_seats": [],
            "blocking_count": len(blocking),
        },
        "seat_check": None,
    }
    save_plan(args, plan)

    if blocking:
        print(f"\n=> {len(blocking)} blocking issue(s) — fix these before continuing.")
    else:
        print("\n=> No blocking issues. Next: list-groups, then suggest-groups.")


def _row_to_plan(r: dict) -> dict:
    return {
        "line": r["_line"],
        "name": r.get("Name", ""),
        "email": r.get("Email", "").lower() if r.get("Email") else "",
        "role": r.get("Role", ""),
        "isActive": r.get("_isActiveParsed", True),
        "userGroup": r.get("UserGroup", "").strip() if r.get("UserGroup") else "",
        "userGroupStatus": "unknown",
    }


def _summarize_groups(plan_rows: list[dict], existing_groups: set[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in plan_rows:
        name = row.get("userGroup", "")
        if not name:
            continue
        out[name] = "existing" if name in existing_groups else "new"
    return out


def cmd_list_groups(client: Client, args: argparse.Namespace) -> None:
    body = client.get(f"{TENANT_BASE}/api/Public/v1/get-user-groups")
    groups = unwrap(body)
    if not groups:
        print("No user groups exist on this tenant yet.")
        return
    print(f"\nUser groups on {client.tenant or '<default tenant>'} ({len(groups)}):")
    for g in groups:
        gid = g.get("id") or g.get("Id")
        name = g.get("name") or g.get("Name") or "<unnamed>"
        print(f"  id={gid:<6}  name={name!r}")


def cmd_list_users(client: Client, args: argparse.Namespace) -> None:
    body = client.get(f"{TENANT_BASE}/api/Public/v1/get-users")
    users = unwrap(body)
    if not users:
        print("No users exist on this tenant yet.")
        return
    print(f"\nUsers on {client.tenant or '<default tenant>'} ({len(users)}):")
    role_counts = Counter(u.get("role") for u in users)
    active_counts = Counter("active" if u.get("isActive") else "inactive" for u in users)
    print(f"  by role:    {dict(role_counts)}")
    print(f"  by status:  {dict(active_counts)}")


def _fetch_existing_groups(client: Client) -> set[str]:
    body = client.get(f"{TENANT_BASE}/api/Public/v1/get-user-groups")
    return {(g.get("name") or g.get("Name") or "") for g in unwrap(body)} - {""}


def cmd_suggest_groups(client: Client, args: argparse.Namespace) -> None:
    plan = load_plan(args)
    existing = _fetch_existing_groups(client)

    rows = plan["rows"]
    populated = [r for r in rows if r.get("userGroup")]
    blank = [r for r in rows if not r.get("userGroup")]

    if blank and not populated:
        print(f"\n{len(blank)} rows have no UserGroup. Suggesting based on email domain.")
        domain_groups: dict[str, list[int]] = {}
        for i, r in enumerate(rows):
            domain = r["email"].split("@", 1)[-1] if "@" in r.get("email", "") else "(no domain)"
            domain_groups.setdefault(domain, []).append(i)

        if len(domain_groups) == 1:
            domain = next(iter(domain_groups))
            stem = domain.split(".")[0].title()
            print(f"  All {len(rows)} rows share the {domain} domain. "
                  f"Suggested single group: {stem!r} (the agent will confirm with the user).")
        else:
            print(f"  {len(domain_groups)} distinct domains:")
            for domain, idxs in domain_groups.items():
                print(f"    {domain}: {len(idxs)} rows")

    elif populated and blank:
        print(f"\n{len(populated)} rows have UserGroup set, {len(blank)} are blank.")

    plan["groups"] = _summarize_groups(rows, existing)
    new_groups = [name for name, status in plan["groups"].items() if status == "new"]
    existing_groups = [name for name, status in plan["groups"].items() if status == "existing"]

    print(f"\nGroups in plan: {len(plan['groups'])} distinct")
    if existing_groups:
        print(f"  existing in tenant ({len(existing_groups)}): {sorted(existing_groups)}")
    if new_groups:
        print(f"  NEW (would be auto-created on import) ({len(new_groups)}): {sorted(new_groups)}")
        print("  ^ Each NEW group will be created with the canned description")
        print('    "This User Group has been created from a CSV file. Please update the description."')
        print("  Have the user explicitly confirm each NEW group before continuing.")

    save_plan(args, plan)


def cmd_check_duplicates(client: Client, args: argparse.Namespace) -> None:
    plan = load_plan(args)
    existing_users = unwrap(client.get(f"{TENANT_BASE}/api/Public/v1/get-users"))
    existing_emails = {(u.get("email") or "").lower() for u in existing_users} - {""}

    duplicates = []
    for row in plan["rows"]:
        if row["email"] and row["email"].lower() in existing_emails:
            duplicates.append({"line": row["line"], "email": row["email"], "name": row["name"]})

    plan.setdefault("validation", {})["duplicates_found"] = duplicates
    save_plan(args, plan)

    if not duplicates:
        print(f"\nNo duplicates. {len(plan['rows'])} rows do not collide with existing tenant users.")
        return

    print(f"\nSTOP — {len(duplicates)} email(s) already exist in this tenant:")
    for d in duplicates:
        print(f"  row {d['line']:>3}: {d['email']!r} ({d['name']})")
    print("\nThe agent should ask the user one of:")
    print("  (a) 'I will edit the file and remove these — re-run the skill afterward.' → exit")
    print("  (b) 'Drop these duplicates from the planned import and continue.'        → "
          f"run `python3 {sys.argv[0]} drop-duplicates [--tenant ...]`")


def cmd_drop_duplicates(client: Client, args: argparse.Namespace) -> None:
    plan = load_plan(args)
    duplicates = plan.get("validation", {}).get("duplicates_found", [])
    if not duplicates:
        print("No duplicates flagged. Nothing to drop.")
        return
    dup_emails = {d["email"].lower() for d in duplicates}
    before = len(plan["rows"])
    plan["rows"] = [r for r in plan["rows"] if r["email"].lower() not in dup_emails]
    plan["validation"]["duplicates_dropped"] = duplicates
    plan["validation"]["duplicates_found"] = []
    print(f"\nDropped {before - len(plan['rows'])} duplicate row(s). Plan now has {len(plan['rows'])} rows.")
    save_plan(args, plan)


def _seat_cap(tenant: str | None) -> int | None:
    """Read the seat cap from ITERO_TENANT_SEATS_<NAME> in env. Returns None if not set.

    The seat field is not exposed on the public API yet — see itero_app_user.md.
    """
    if tenant:
        raw = os.getenv(f"ITERO_TENANT_SEATS_{tenant.upper()}")
    else:
        raw = os.getenv("ITERO_TENANT_SEATS")
    if raw is None:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def cmd_check_seats(client: Client, args: argparse.Namespace) -> None:
    plan = load_plan(args)
    cap = _seat_cap(client.tenant)

    existing_users = unwrap(client.get(f"{TENANT_BASE}/api/Public/v1/get-users"))
    current_active_reps = sum(
        1 for u in existing_users
        if u.get("isActive") and u.get("role") == "Representative"
    )
    plan_active_reps = sum(
        1 for r in plan["rows"]
        if r.get("isActive") and r.get("role") == "Representative"
    )

    plan["seat_check"] = {
        "currentActiveReps": current_active_reps,
        "activeRepsInPlan": plan_active_reps,
        "totalSeats": cap,
        "ok": (cap is None) or (current_active_reps + plan_active_reps <= cap),
    }
    save_plan(args, plan)

    if cap is None:
        env_var = f"ITERO_TENANT_SEATS_{client.tenant}" if client.tenant else "ITERO_TENANT_SEATS"
        print(f"\nSeat cap unknown — {env_var} is not set in .env.")
        print("  The public API does not expose tenant.NumberOfSeats. Skipping the seat check.")
        print(f"  Current active reps: {current_active_reps}. New active reps in plan: {plan_active_reps}.")
        return

    total = current_active_reps + plan_active_reps
    print(f"\nTenant seats: {cap}")
    print(f"  Currently filled (active Reps): {current_active_reps}")
    print(f"  New active Reps in plan:        {plan_active_reps}")
    print(f"  Total after import:             {total}")
    if total > cap:
        over = total - cap
        print(f"\nSTOP — would exceed the seat cap by {over}.")
        print("  Ask the user to either:")
        print(f"    (a) Set IsActive=false on {over} new Rep row(s) in the plan, then re-run this check.")
        print("    (b) Abort and contact Itero to add seats.")
    else:
        print(f"\nOK — {cap - total} seat(s) remaining after import.")


def _build_csv_bytes(plan: dict) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Name", "Email", "Role", "IsActive", "UserGroup"])
    for r in plan["rows"]:
        writer.writerow([
            r["name"],
            r["email"],
            r["role"],
            "true" if r.get("isActive", True) else "false",
            r.get("userGroup", ""),
        ])
    return buf.getvalue().encode("utf-8")


def cmd_preview(client: Client | None, args: argparse.Namespace) -> None:
    plan = load_plan(args)
    rows = plan["rows"]
    role_counts = Counter(r["role"] for r in rows)
    active_counts = Counter("active" if r.get("isActive") else "inactive" for r in rows)
    group_counts = Counter(r.get("userGroup") or "(no group)" for r in rows)

    print(f"\nPlan: {len(rows)} row(s) ready to import")
    print(f"  Role mix:    {dict(role_counts)}")
    print(f"  Status mix:  {dict(active_counts)}")
    print(f"  Group mix:")
    for group, count in group_counts.most_common():
        status = plan.get("groups", {}).get(group, "—")
        print(f"    {group!r:<30}  {count:>3} ({status})")

    csv_bytes = _build_csv_bytes(plan)
    print(f"\nCSV bytes that will be uploaded: {len(csv_bytes)}")
    print("First 5 lines:")
    for line in csv_bytes.decode("utf-8").splitlines()[:5]:
        print(f"  {line}")

    seat = plan.get("seat_check") or {}
    if seat.get("ok") is False:
        print("\nWARNING: seat_check.ok is False — re-run check-seats and resolve before import.")

    print("\nWhen the user confirms with `yes`, run:")
    print(f"  python3 {sys.argv[0]} import [--tenant ...] --live")


def cmd_import(client: Client, args: argparse.Namespace) -> None:
    plan = load_plan(args)
    rows = plan["rows"]
    if not rows:
        raise SystemExit("plan has no rows to import.")

    seat = plan.get("seat_check") or {}
    if seat.get("ok") is False:
        raise SystemExit(
            "seat_check.ok is False. Resolve the seat overflow (run check-seats again) "
            "before retrying the import."
        )
    blocking = [
        i for i in plan.get("validation", {}).get("issues", [])
        if i.get("kind") in ("missing_column", "missing_value", "bad_email", "bad_role", "too_long", "bad_isactive")
    ]
    if blocking:
        raise SystemExit(
            f"plan has {len(blocking)} blocking validation issue(s). "
            "Re-run inspect after fixing them in the plan."
        )

    csv_bytes = _build_csv_bytes(plan)
    url = f"{TENANT_BASE}/api/public/v1/user/import-csv"
    result = client.post_multipart(url, filename="users.csv", content=csv_bytes)

    if client.dry_run:
        print(f"\n[DRY-RUN] would have uploaded {len(csv_bytes)} bytes ({len(rows)} users) to {url}")
        print("Re-run with --live to actually submit.")
        return

    print(f"\n200 OK — imported {len(rows)} user(s).")
    new_groups = [n for n, s in plan.get("groups", {}).items() if s == "new"]
    if new_groups:
        print(f"  Server auto-created {len(new_groups)} new group(s): {sorted(new_groups)}")


# ---------------------------------------------------------------------------
# Argparse wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tenant", help="Resolve ITERO_API_KEY_<TENANT> instead of bare ITERO_API_KEY")
    common.add_argument("--plan", help=f"Path to plan json (default: {DEFAULT_PLAN_PATH})")

    p = argparse.ArgumentParser(prog="upload_users", description=__doc__, parents=[common])
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("inspect", parents=[common], help="Parse a CSV and write the initial plan.")
    s.add_argument("csv")

    sub.add_parser("list-groups", parents=[common], help="List user groups on the tenant.")
    sub.add_parser("list-users", parents=[common], help="List users on the tenant.")
    sub.add_parser("suggest-groups", parents=[common], help="Propose UserGroup assignments based on signals.")
    sub.add_parser("check-duplicates", parents=[common], help="Cross-reference plan emails against tenant users.")
    sub.add_parser("drop-duplicates", parents=[common], help="Drop rows flagged by check-duplicates.")
    sub.add_parser("check-seats", parents=[common], help="Compute seat math against ITERO_TENANT_SEATS_<TENANT>.")
    sub.add_parser("preview", parents=[common], help="Print the final plan summary and the CSV bytes.")

    s = sub.add_parser("import", parents=[common],
                       help="POST the plan as a CSV. Dry-run unless --live is passed.")
    s.add_argument("--live", action="store_true", help="Actually submit the multipart POST.")

    return p


def main() -> None:
    args = build_parser().parse_args()

    needs_client = args.command not in ("inspect", "preview")
    if needs_client:
        dry_run = not getattr(args, "live", False)
        client = Client(tenant=args.tenant, dry_run=dry_run)
    else:
        client = None

    dispatch = {
        "inspect": cmd_inspect,
        "list-groups": cmd_list_groups,
        "list-users": cmd_list_users,
        "suggest-groups": cmd_suggest_groups,
        "check-duplicates": cmd_check_duplicates,
        "drop-duplicates": cmd_drop_duplicates,
        "check-seats": cmd_check_seats,
        "preview": cmd_preview,
        "import": cmd_import,
    }
    dispatch[args.command](client, args)


if __name__ == "__main__":
    main()
