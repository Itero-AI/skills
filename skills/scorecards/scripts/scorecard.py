#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.28",
#     "python-dotenv>=1.0",
# ]
# ///
"""
Itero scorecard skill — CLI.

All write subcommands are dry-run by default. Pass --live to execute.
Pass --tenant NAME to use ITERO_API_KEY_NAME; omit for bare ITERO_API_KEY.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from scorecard_client import Client, PRACTICE_BASE, unwrap, pick_id

TENANT_BASE = "https://iterotenantapi.azurewebsites.net"
CONFIG_PATH = Path(os.environ.get("CLAUDE_PLUGIN_DATA", str(Path(__file__).parent.parent))) / ".scorecard-config.json"


def _find_template_by_id(client: Client, template_id: str) -> dict:
    templates = unwrap(client.get(f"{PRACTICE_BASE}/api/public/v1/scorecard"))
    t = next((x for x in templates if str(pick_id(x)) == str(template_id)), None)
    if not t:
        names = ", ".join(
            f"id={pick_id(x)} name={x.get('name')!r}" for x in templates
        )
        raise SystemExit(
            f"template id={template_id} not found. Available: {names or 'none'}"
        )
    return t


def _get_categories(client: Client, template_id: int | str) -> list[dict]:
    cats: list[dict] = []
    for sc_type in (0, 1):
        cats.extend(unwrap(client.get(
            f"{PRACTICE_BASE}/api/public/v1/scorecard-category",
            params={"scorecardTemplateId": template_id, "type": sc_type},
        )))
    return cats


def _get_criteria(client: Client, category_id: int | str) -> list[dict]:
    return unwrap(client.get(
        f"{PRACTICE_BASE}/api/public/v1/scorecard-criteria",
        params={"templateCategoryId": category_id},
    ))


def _get_rubrics(client: Client, criteria_id: int | str) -> list[dict]:
    return unwrap(client.get(
        f"{PRACTICE_BASE}/api/public/v1/scorecard-criteria/rubrics",
        params={"criteriaId": criteria_id},
    ))


def cmd_list(client: Client, args: argparse.Namespace) -> None:
    templates = unwrap(client.get(f"{PRACTICE_BASE}/api/public/v1/scorecard"))
    if not templates:
        print("No templates found on this tenant.")
        return
    print(f"\nTemplates ({len(templates)}):")
    for t in templates:
        tid = pick_id(t)
        name = t.get("name") or t.get("Name") or "<unnamed>"
        qual = t.get("qualitiveAgentId") or 0
        qa = t.get("qaAgentId") or 0
        print(f"  id={tid:<6}  name={name!r}  qualAgent={qual}  qaAgent={qa}")


def cmd_fetch(client: Client, args: argparse.Namespace) -> None:
    template = _find_template_by_id(client, args.id)
    template_id = pick_id(template)

    categories = _get_categories(client, template_id)
    # Fetch all criteria for every category before fetching any rubrics,
    # so the API call order is: categories → all criteria → all rubrics.
    for cat in categories:
        cat["criteria"] = _get_criteria(client, pick_id(cat))
    for cat in categories:
        for crit in cat["criteria"]:
            crit["rubrics"] = _get_rubrics(client, pick_id(crit))

    template["categories"] = categories
    print(json.dumps(template, indent=2, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Agent ID resolution
#
# Config is tenant-keyed: top-level keys are tenant names (upper-case),
# 'DEFAULT' for the no-tenant case. Each tenant entry has its own
# {qaAgentId, qualitiveAgentIds} since agent IDs are tenant-scoped on the
# Itero practice API — sharing one cache across tenants causes 500s.
#
# Legacy flat format (top-level qaAgentId/qualitiveAgentIds) is auto-migrated
# into the 'DEFAULT' entry on first read.
# ---------------------------------------------------------------------------

def _tenant_key(tenant: str | None) -> str:
    return (tenant or "DEFAULT").upper()


def load_config() -> dict:
    """Return tenant-keyed config dict. Migrates legacy flat format into DEFAULT."""
    if not CONFIG_PATH.exists():
        return {}
    cfg = json.loads(CONFIG_PATH.read_text())
    if "qaAgentId" in cfg or "qualitiveAgentIds" in cfg:
        legacy = {
            "qaAgentId": cfg.get("qaAgentId"),
            "qualitiveAgentIds": cfg.get("qualitiveAgentIds") or {},
        }
        migrated = {k: v for k, v in cfg.items()
                    if k not in ("qaAgentId", "qualitiveAgentIds")}
        migrated["DEFAULT"] = legacy
        return migrated
    return cfg


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2))


def resolve_agent_ids(client: Client, agent_type: str, tenant: str | None) -> tuple[int, int]:
    """Return (qualitiveAgentId, qaAgentId) for the given tenant. Config first; donor scan fallback; agent-catalog fallback."""
    config = load_config()
    tkey = _tenant_key(tenant)
    tcfg = config.get(tkey, {})
    qa_id = tcfg.get("qaAgentId")
    qual_id = (tcfg.get("qualitiveAgentIds") or {}).get(agent_type)
    if not qual_id:
        qual_id = (tcfg.get("qualitiveAgentIds") or {}).get("other")

    if qa_id and qual_id:
        return int(qual_id), int(qa_id)

    # Donor scan — borrow IDs from an existing template in THIS tenant
    templates = unwrap(client.get(f"{PRACTICE_BASE}/api/public/v1/scorecard"))
    for t in templates:
        q = t.get("qualitiveAgentId") or t.get("QualitiveAgentId") or 0
        a = t.get("qaAgentId") or t.get("QaAgentId") or 0
        if q and a:
            print(f"  donor template id={pick_id(t)}  name={t.get('name')!r}  (tenant={tkey})")
            qual_id, qa_id = int(q), int(a)
            cfg = load_config()
            tcfg = cfg.setdefault(tkey, {})
            tcfg.setdefault("qualitiveAgentIds", {})[agent_type] = qual_id
            tcfg["qaAgentId"] = qa_id
            save_config(cfg)
            print(f"  saved agent IDs to {CONFIG_PATH.name} under tenant={tkey}")
            return qual_id, qa_id

    # Agent-catalog fallback — for fresh tenants where no donor template exists
    print(
        f"\nNo existing template with agent IDs found on tenant={tkey}.\n"
        "Fetching the tenant agent catalog to help you pick qual + QA agents...\n"
    )
    try:
        agents = unwrap(client.get(f"{TENANT_BASE}/api/public/v1/agent"))
    except SystemExit:
        agents = []
    if agents:
        print(f"Agent catalog ({len(agents)} agents):")
        for a in agents:
            aid = a.get("id") or a.get("Id") or "?"
            name = a.get("name") or a.get("Name") or "<unnamed>"
            atype = a.get("agentType") or a.get("type") or a.get("Type") or ""
            print(f"  id={aid:<6}  name={name!r}  type={atype!r}")
        print(
            "\nAdd the chosen IDs to .scorecard-config.json under the "
            f'"{tkey}" key, e.g.:\n'
            "  {\n"
            f'    "{tkey}": {{\n'
            '      "qaAgentId": <QA agent id>,\n'
            '      "qualitiveAgentIds": {"other": <qual agent id>}\n'
            "    }\n"
            "  }\n"
            "Then re-run the create command."
        )
    else:
        print(
            "Could not fetch agent catalog — check your API key and network.\n"
            "Provide qualitiveAgentId and qaAgentId manually in .scorecard-config.json."
        )
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# Subcommand: create
# ---------------------------------------------------------------------------

def cmd_create(client: Client, args: argparse.Namespace) -> None:
    plan_path = Path(args.plan)
    if not plan_path.exists():
        raise SystemExit(f"plan file not found: {plan_path}")
    plan = json.loads(plan_path.read_text())

    agent_type = plan.get("agentType", "other")
    qual_agent_id, qa_agent_id = resolve_agent_ids(client, agent_type, args.tenant)

    # Build template payload
    template_payload: dict = {
        "name": plan["name"],
        "qualitiveAgentId": qual_agent_id,
        "qaAgentId": qa_agent_id,
    }
    for opt in ("callTypes", "practiceScenarioCallTypeIds", "meetingKeywords",
                "callTags", "maxCallDurationSeconds", "minCallDurationSeconds", "userGroupIds"):
        if opt in plan:
            template_payload[opt] = plan[opt]

    created_template = client.post(f"{PRACTICE_BASE}/api/public/v1/scorecard", template_payload)
    template_id = pick_id(created_template)
    print(f"\nCreated template: id={template_id}  name={plan['name']!r}")

    total_criteria = 0
    for cat_def in plan.get("categories", []):
        cat_payload = {
            "name": cat_def["name"],
            "scorecardTemplateId": template_id,
            "scorecardType": cat_def["scorecardType"],
        }
        created_cat = client.post(
            f"{PRACTICE_BASE}/api/public/v1/scorecard-category", cat_payload
        )
        cat_id = pick_id(created_cat)
        print(f"  Created category: id={cat_id}  name={cat_def['name']!r}")

        for crit_def in cat_def.get("criteria", []):
            crit_payload = {
                "title": crit_def["title"],
                "criteria": crit_def["criteria"],
                "scorecardTemplateCategoryId": cat_id,
            }
            created_crit = client.post(
                f"{PRACTICE_BASE}/api/public/v1/scorecard-criteria", crit_payload
            )
            crit_id = pick_id(created_crit)
            print(f"    Created criterion: id={crit_id}  title={crit_def['title']!r}")
            total_criteria += 1

    print(f"\nDone: {len(plan.get('categories', []))} categories, {total_criteria} criteria")


# ---------------------------------------------------------------------------
# Subcommand: add-category
# ---------------------------------------------------------------------------

def cmd_add_category(client: Client, args: argparse.Namespace) -> None:
    payload = json.loads(args.json)
    created = client.post(f"{PRACTICE_BASE}/api/public/v1/scorecard-category", payload)
    cat_id = pick_id(created)
    print(f"\nCreated category: id={cat_id}  name={payload.get('name')!r}")


# ---------------------------------------------------------------------------
# Subcommand: add-criteria
# ---------------------------------------------------------------------------

def cmd_add_criteria(client: Client, args: argparse.Namespace) -> None:
    payload = json.loads(args.json)
    created = client.post(f"{PRACTICE_BASE}/api/public/v1/scorecard-criteria", payload)
    crit_id = pick_id(created)
    print(f"\nCreated criterion: id={crit_id}  title={payload.get('title')!r}")


# ---------------------------------------------------------------------------
# Subcommand: update
# ---------------------------------------------------------------------------

def cmd_update(client: Client, args: argparse.Namespace) -> None:
    entity = args.entity
    entity_id = int(args.id)
    payload = json.loads(args.json)
    payload["id"] = entity_id  # ensure id is present regardless of what caller sent

    url_map = {
        "template": f"{PRACTICE_BASE}/api/public/v1/scorecard",
        "category": f"{PRACTICE_BASE}/api/public/v1/scorecard-category",
        "criteria": f"{PRACTICE_BASE}/api/public/v1/scorecard-criteria",
    }
    if entity not in url_map:
        raise SystemExit(f"unknown entity '{entity}'. Use: template, category, criteria")

    client.put(url_map[entity], payload)
    print(f"\nUpdated {entity} id={entity_id}")


# ---------------------------------------------------------------------------
# Subcommand: update-rubric
# ---------------------------------------------------------------------------

def cmd_update_rubric(client: Client, args: argparse.Namespace) -> None:
    payload = {"id": int(args.id), "description": args.description}
    client.put(f"{PRACTICE_BASE}/api/public/v1/scorecard-criteria/rubric", payload)
    print(f"\nUpdated rubric id={args.id}")


# ---------------------------------------------------------------------------
# Subcommand: delete
# ---------------------------------------------------------------------------

def _delete_single_criteria(client: Client, criteria_id: int | str) -> None:
    client.delete(f"{PRACTICE_BASE}/api/public/v1/scorecard-criteria/{criteria_id}")
    print(f"  Deleted criterion id={criteria_id}")


def cmd_delete(client: Client, args: argparse.Namespace) -> None:
    entity = args.entity
    entity_id = int(args.id)

    if entity == "criteria":
        _delete_single_criteria(client, entity_id)
        print(f"\nDeleted criterion id={entity_id}")

    elif entity == "category":
        criteria = _get_criteria(client, entity_id)
        for crit in criteria:
            _delete_single_criteria(client, pick_id(crit))
        client.delete(f"{PRACTICE_BASE}/api/public/v1/scorecard-category/{entity_id}")
        print(f"\nDeleted category id={entity_id} ({len(criteria)} criteria removed)")

    elif entity == "template":
        # Fetch all categories (both scorecard types) before deleting anything
        all_categories: list[dict] = []
        for sc_type in (0, 1):
            all_categories.extend(unwrap(client.get(
                f"{PRACTICE_BASE}/api/public/v1/scorecard-category",
                params={"scorecardTemplateId": entity_id, "type": sc_type},
            )))
        total_criteria = 0
        for cat in all_categories:
            cat_id = pick_id(cat)
            criteria = _get_criteria(client, cat_id)
            for crit in criteria:
                _delete_single_criteria(client, pick_id(crit))
                total_criteria += 1
            client.delete(f"{PRACTICE_BASE}/api/public/v1/scorecard-category/{cat_id}")
        client.delete(f"{PRACTICE_BASE}/api/public/v1/scorecard/{entity_id}")
        print(f"\nDeleted template id={entity_id} ({total_criteria} criteria removed)")

    else:
        raise SystemExit(f"unknown entity '{entity}'. Use: criteria, category, template")


def build_parser() -> argparse.ArgumentParser:
    # Shared flags available on the top-level parser AND every subparser,
    # so `--tenant` / `--live` work on either side of the subcommand name.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--tenant", default=None)
    common.add_argument("--live", action="store_true")

    p = argparse.ArgumentParser(
        prog="scorecard.py",
        description="Itero scorecard CRUD — templates, categories, criteria, rubrics.",
        parents=[common],
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("list", parents=[common])

    fetch_p = sub.add_parser("fetch", parents=[common])
    fetch_p.add_argument("id")

    create_p = sub.add_parser("create", parents=[common])
    create_p.add_argument("plan")

    add_cat_p = sub.add_parser("add-category", parents=[common])
    add_cat_p.add_argument("json")

    add_crit_p = sub.add_parser("add-criteria", parents=[common])
    add_crit_p.add_argument("json")

    update_p = sub.add_parser("update", parents=[common])
    update_p.add_argument("entity", choices=["template", "category", "criteria"])
    update_p.add_argument("id")
    update_p.add_argument("json")

    rubric_p = sub.add_parser("update-rubric", parents=[common])
    rubric_p.add_argument("id")
    rubric_p.add_argument("description")

    delete_p = sub.add_parser("delete", parents=[common])
    delete_p.add_argument("entity", choices=["criteria", "category", "template"])
    delete_p.add_argument("id")

    return p


def main() -> None:
    args = build_parser().parse_args()
    client = Client(tenant=args.tenant, dry_run=not args.live)
    dispatch = {
        "list": cmd_list,
        "fetch": cmd_fetch,
        "create": cmd_create,
        "add-category": cmd_add_category,
        "add-criteria": cmd_add_criteria,
        "update": cmd_update,
        "update-rubric": cmd_update_rubric,
        "delete": cmd_delete,
    }
    dispatch[args.command](client, args)


if __name__ == "__main__":
    main()
