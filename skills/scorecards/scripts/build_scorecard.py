#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pydantic>=2.7,<3",
#     "python-dotenv>=1.0,<2",
#     "requests>=2.31,<3",
# ]
# ///
"""Build an Itero scorecard from a validated JSON plan.

Builds are dry-run by default. Pass ``--live`` to issue writes. Validation is
fully offline and runs before credentials or an HTTP client are initialized.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Literal, Protocol

import requests
from dotenv import load_dotenv
from pydantic import (
    BaseModel,
    ConfigDict,
    ValidationError,
)

GATEWAY_BASE = "https://iterogatewayapi.azurewebsites.net"
API_PREFIX = "/api/public/v1"
AGENT_PATH = f"{API_PREFIX}/agent"
SCORECARD_PATH = f"{API_PREFIX}/scorecard"
CATEGORY_PATH = f"{API_PREFIX}/scorecard-category"
CRITERION_PATH = f"{API_PREFIX}/scorecard-criteria"
RUBRIC_PATH = f"{CRITERION_PATH}/rubric"
RUBRICS_PATH = f"{CRITERION_PATH}/rubrics"
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

Output = Callable[[str], None]


class ScorecardError(Exception):
    """Base class for expected builder failures."""


class PlanFileError(ScorecardError):
    """Raised when a plan or journal cannot be read safely."""


class ApiError(ScorecardError):
    """Raised when the gateway request fails or returns an invalid response."""


class AgentResolutionError(ScorecardError):
    """Raised when omitted agent IDs cannot be selected unambiguously."""


class JournalError(ScorecardError):
    """Raised when journal state makes a build unsafe to continue."""


class CleanupCancelled(ScorecardError):
    """Raised when a live cleanup is not explicitly confirmed."""


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RubricPlan(StrictModel):
    scale: Literal[0, 1, 2, 3, 4, 5]
    description: str


class CriterionPlan(StrictModel):
    title: str
    criteria: str
    rubrics: list[RubricPlan] = []


class CategoryPlan(StrictModel):
    name: str
    weight: int
    scorecardType: Literal[0, 1]
    criteria: list[CriterionPlan]


class ScorecardPlan(StrictModel):
    name: str
    callTypes: list[Literal[0, 1, 2]]
    interactionType: Literal[0, 1]
    userGroupIds: list[int] | None = None
    qualitiveAgentId: int | None = None
    qaAgentId: int | None = None
    categories: list[CategoryPlan]
    publish: bool


class Transport(Protocol):
    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Issue an HTTP request and return a response-like object."""


class RequestsTransport:
    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        return requests.request(method, url, **kwargs)


def _response_id(body: Any) -> int | str | None:
    if not isinstance(body, Mapping):
        return None
    direct_id = body.get("id") or body.get("Id")
    if direct_id is not None:
        return direct_id
    data = body.get("data")
    if isinstance(data, Mapping):
        return data.get("id") or data.get("Id")
    return None


def _unwrap_list(body: Any) -> list[dict[str, Any]]:
    if isinstance(body, list):
        return [item for item in body if isinstance(item, dict)]
    if isinstance(body, Mapping):
        for key in ("data", "items"):
            value = body.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    raise ApiError("gateway response did not contain the expected list")


class GatewayClient:
    """Gateway client with injectable transport and a strict dry-run write gate."""

    def __init__(
        self,
        api_key: str,
        *,
        dry_run: bool = True,
        transport: Transport | None = None,
        output: Output = print,
    ) -> None:
        if not api_key:
            raise ApiError("the API key is empty")
        self._api_key = api_key
        self.dry_run = dry_run
        self.transport = transport or RequestsTransport()
        self.output = output
        self._dry_run_id = 0

    @classmethod
    def from_environment(
        cls,
        tenant: str | None = None,
        *,
        dry_run: bool = True,
        transport: Transport | None = None,
        output: Output = print,
    ) -> GatewayClient:
        load_dotenv()
        env_name = f"ITERO_API_KEY_{tenant.upper()}" if tenant else "ITERO_API_KEY"
        api_key = os.getenv(env_name)
        if not api_key:
            raise ApiError(f"missing environment variable {env_name}")
        return cls(api_key, dry_run=dry_run, transport=transport, output=output)

    def get(self, path: str, *, params: Mapping[str, Any] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def write(
        self, method: str, path: str, *, payload: Mapping[str, Any] | None = None
    ) -> Any:
        normalized_method = method.upper()
        if normalized_method not in WRITE_METHODS:
            raise ApiError(f"unsupported write method {normalized_method}")
        return self._request(normalized_method, path, payload=payload)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> Any:
        if not path.startswith("/api/public/v1/"):
            raise ApiError(f"refusing request outside the public v1 gateway: {path}")

        self.output(f"{method} {path}")
        if payload is not None:
            self.output(
                f"  payload: {json.dumps(payload, ensure_ascii=False, sort_keys=True)}"
            )

        if self.dry_run and method in WRITE_METHODS:
            self.output("  [DRY-RUN] write skipped")
            self._dry_run_id += 1
            if method == "POST":
                return {"id": f"DRY-RUN-{self._dry_run_id}"}
            return {}

        kwargs: dict[str, Any] = {
            "headers": {
                "X-API-Key": self._api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            "timeout": 30,
        }
        if params is not None:
            kwargs["params"] = dict(params)
        if payload is not None:
            kwargs["json"] = dict(payload)

        try:
            response = self.transport.request(method, f"{GATEWAY_BASE}{path}", **kwargs)
        except Exception as exc:
            raise ApiError(f"{method} {path} could not reach the gateway") from exc

        if isinstance(response, (Mapping, list)):
            return response

        status_code = getattr(response, "status_code", None)
        if not isinstance(status_code, int):
            raise ApiError(f"{method} {path} returned an invalid transport response")
        if not 200 <= status_code < 300:
            response_text = str(getattr(response, "text", ""))[:800]
            safe_text = response_text.replace(self._api_key, "[redacted]")
            detail = f": {safe_text}" if safe_text else ""
            raise ApiError(f"{method} {path} returned HTTP {status_code}{detail}")
        if not getattr(response, "text", ""):
            return {}
        try:
            return response.json()
        except (TypeError, ValueError) as exc:
            raise ApiError(f"{method} {path} returned invalid JSON") from exc


class Journal:
    """Crash journal persisted before every live write."""

    def __init__(self, path: Path, *, enabled: bool, force_new: bool = False) -> None:
        self.path = path
        self.enabled = enabled
        if path.exists() and not force_new:
            raise JournalError(
                f"journal already exists at {path}; clean it up or pass --force-new"
            )
        self.entries: list[dict[str, Any]] = []
        if enabled and force_new:
            self._save()

    def begin(self, *, step: str, method: str, path: str, name: str) -> int | None:
        if not self.enabled:
            return None
        self.entries.append(
            {
                "step": step,
                "method": method,
                "path": path,
                "name": name,
                "status": "unconfirmed",
            }
        )
        self._save()
        return len(self.entries) - 1

    def succeed(self, index: int | None, entity_id: int | str | None) -> None:
        if index is None:
            return
        self.entries[index]["status"] = "succeeded"
        if entity_id is not None:
            self.entries[index]["id"] = entity_id
        self._save()

    def render(self) -> str:
        return json.dumps(self.entries, indent=2, ensure_ascii=False)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=self.path.parent, delete=False
        ) as temporary:
            json.dump(self.entries, temporary, indent=2, ensure_ascii=False)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        temporary_path.replace(self.path)


def journal_path_for(plan_path: Path) -> Path:
    return Path(f"{plan_path}.journal.json")


def load_plan(plan_path: Path) -> ScorecardPlan:
    try:
        raw = json.loads(plan_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlanFileError(f"plan file not found: {plan_path}") from exc
    except OSError as exc:
        raise PlanFileError(f"could not read plan file {plan_path}") from exc
    except json.JSONDecodeError as exc:
        raise PlanFileError(
            f"invalid JSON in {plan_path} at line {exc.lineno}, column {exc.colno}"
        ) from exc
    try:
        return ScorecardPlan.model_validate(raw)
    except ValidationError as exc:
        raise PlanFileError(f"invalid scorecard plan {plan_path}:\n{exc}") from exc


def _agent_id(agent: Mapping[str, Any]) -> int | None:
    value = agent.get("id") or agent.get("Id")
    return value if isinstance(value, int) and value > 0 else None


def _normalized_agent_name(agent: Mapping[str, Any]) -> str:
    return re.sub(
        r"[^a-z0-9]+", " ", str(agent.get("name") or agent.get("Name") or "").lower()
    ).strip()


def _select_agent(
    agents: Sequence[dict[str, Any]],
    *,
    role: str,
    interaction_type: Literal[0, 1],
    excluded_ids: set[int],
) -> int:
    compatible = [
        agent
        for agent in agents
        if _agent_id(agent) not in excluded_ids
        and agent.get("interactionType", agent.get("InteractionType"))
        in (None, int(interaction_type))
    ]
    if role == "qualitative":
        role_matches = [
            agent
            for agent in compatible
            if any(
                phrase in _normalized_agent_name(agent)
                for phrase in ("qualitative", "qualitive", "coaching")
            )
        ]
        if not role_matches:
            role_matches = [
                agent for agent in compatible if agent.get("agentType") == 0
            ]
    else:
        role_matches = [
            agent
            for agent in compatible
            if re.search(
                r"(^| )qa($| )|quality assurance", _normalized_agent_name(agent)
            )
        ]

    valid_ids = sorted({_agent_id(agent) for agent in role_matches if _agent_id(agent)})
    if len(valid_ids) == 1:
        return valid_ids[0]
    if not role_matches and len(compatible) == 1:
        only_id = _agent_id(compatible[0])
        if only_id is not None:
            return only_id

    candidates = ", ".join(
        f"id={_agent_id(agent)} name={agent.get('name') or agent.get('Name')!r}"
        for agent in compatible
    )
    raise AgentResolutionError(
        f"could not resolve one {role} agent for interactionType={int(interaction_type)}; "
        f"provide its ID explicitly. Compatible agents: {candidates or 'none'}"
    )


def resolve_agent_ids(plan: ScorecardPlan, client: GatewayClient) -> tuple[int, int]:
    qualitive_id = int(plan.qualitiveAgentId) if plan.qualitiveAgentId else None
    qa_id = int(plan.qaAgentId) if plan.qaAgentId else None
    if qualitive_id is not None and qa_id is not None:
        return qualitive_id, qa_id

    agents = _unwrap_list(client.get(AGENT_PATH))
    excluded = {agent_id for agent_id in (qualitive_id, qa_id) if agent_id is not None}
    if qualitive_id is None:
        qualitive_id = _select_agent(
            agents,
            role="qualitative",
            interaction_type=plan.interactionType,
            excluded_ids=excluded,
        )
        excluded.add(qualitive_id)
    if qa_id is None:
        qa_id = _select_agent(
            agents,
            role="QA",
            interaction_type=plan.interactionType,
            excluded_ids=excluded,
        )
    return qualitive_id, qa_id


def _write_with_journal(
    client: GatewayClient,
    journal: Journal,
    *,
    step: str,
    method: str,
    path: str,
    name: str,
    payload: Mapping[str, Any] | None = None,
    known_id: int | str | None = None,
    require_returned_id: bool = False,
) -> tuple[Any, int | str | None]:
    entry_index = journal.begin(step=step, method=method, path=path, name=name)
    response = client.write(method, path, payload=payload)
    returned_id = _response_id(response) or known_id
    if require_returned_id and returned_id is None:
        raise ApiError(f"{method} {path} succeeded but returned no entity ID")
    journal.succeed(entry_index, returned_id)
    return response, returned_id


def _rubric_scale(rubric: Mapping[str, Any]) -> int | None:
    value = rubric.get("rubrikScale", rubric.get("RubrikScale", rubric.get("scale")))
    return value if isinstance(value, int) else None


def _update_rubrics(
    client: GatewayClient,
    journal: Journal,
    *,
    criterion_id: int | str,
    criterion_name: str,
    rubrics: Sequence[RubricPlan],
) -> None:
    if not rubrics:
        return
    if client.dry_run:
        client.output(
            f"GET {RUBRICS_PATH} (deferred in dry-run until criterion {criterion_id} exists)"
        )
        for rubric in rubrics:
            client.output(
                f"PUT {RUBRIC_PATH} for {criterion_name!r}, scale={int(rubric.scale)}"
            )
            client.output("  [DRY-RUN] write skipped")
        return

    existing = _unwrap_list(
        client.get(RUBRICS_PATH, params={"criteriaId": criterion_id})
    )
    by_scale = {_rubric_scale(rubric): rubric for rubric in existing}
    missing_scales = [
        int(rubric.scale) for rubric in rubrics if int(rubric.scale) not in by_scale
    ]
    if missing_scales:
        raise ApiError(
            f"criterion {criterion_id} returned no rubrics for scales {missing_scales}"
        )

    for rubric in rubrics:
        existing_rubric = by_scale[int(rubric.scale)]
        rubric_id = _response_id(existing_rubric)
        if rubric_id is None:
            raise ApiError(
                f"rubric scale {int(rubric.scale)} for criterion {criterion_id} has no ID"
            )
        _write_with_journal(
            client,
            journal,
            step="rubric",
            method="PUT",
            path=RUBRIC_PATH,
            name=f"{criterion_name} scale {int(rubric.scale)}",
            payload={"id": rubric_id, "description": rubric.description},
            known_id=rubric_id,
        )


class BuildResult(BaseModel):
    template_id: int | str
    category_count: int
    criterion_count: int
    published: bool
    journal_path: Path


def build_scorecard(
    plan: ScorecardPlan,
    client: GatewayClient,
    journal_path: Path,
    *,
    force_new: bool = False,
    output: Output = print,
) -> BuildResult:
    """Execute the ordered scorecard chain, stopping at the first failure."""

    journal = Journal(journal_path, enabled=not client.dry_run, force_new=force_new)
    try:
        qualitive_agent_id, qa_agent_id = resolve_agent_ids(plan, client)
        template_payload: dict[str, Any] = {
            "name": plan.name,
            "callTypes": [int(value) for value in plan.callTypes],
            "interactionType": int(plan.interactionType),
            "qualitiveAgentId": qualitive_agent_id,
            "qaAgentId": qa_agent_id,
        }
        if plan.userGroupIds is not None:
            template_payload["userGroupIds"] = [
                int(value) for value in plan.userGroupIds
            ]

        _, template_id = _write_with_journal(
            client,
            journal,
            step="template",
            method="POST",
            path=SCORECARD_PATH,
            name=plan.name,
            payload=template_payload,
            require_returned_id=True,
        )
        assert template_id is not None

        category_count = 0
        criterion_count = 0
        for category in plan.categories:
            _, category_id = _write_with_journal(
                client,
                journal,
                step="category",
                method="POST",
                path=CATEGORY_PATH,
                name=category.name,
                payload={
                    "name": category.name,
                    "weight": category.weight,
                    "scorecardType": int(category.scorecardType),
                    "scorecardTemplateId": template_id,
                },
                require_returned_id=True,
            )
            assert category_id is not None
            category_count += 1

            for criterion in category.criteria:
                _, criterion_id = _write_with_journal(
                    client,
                    journal,
                    step="criterion",
                    method="POST",
                    path=CRITERION_PATH,
                    name=criterion.title,
                    payload={
                        "title": criterion.title,
                        "criteria": criterion.criteria,
                        "scorecardTemplateCategoryId": category_id,
                    },
                    require_returned_id=True,
                )
                assert criterion_id is not None
                criterion_count += 1
                _update_rubrics(
                    client,
                    journal,
                    criterion_id=criterion_id,
                    criterion_name=criterion.title,
                    rubrics=criterion.rubrics,
                )

        if plan.publish:
            _write_with_journal(
                client,
                journal,
                step="publish",
                method="PATCH",
                path=f"{SCORECARD_PATH}/{template_id}/status",
                name=plan.name,
                payload={"status": 1},
                known_id=template_id,
            )

        return BuildResult(
            template_id=template_id,
            category_count=category_count,
            criterion_count=criterion_count,
            published=plan.publish,
            journal_path=journal_path,
        )
    except Exception:
        output("Build failed. Journal follows:")
        output(journal.render())
        raise


def _load_journal(path: Path) -> list[dict[str, Any]]:
    try:
        body = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlanFileError(f"journal file not found: {path}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise PlanFileError(f"could not read journal file {path}") from exc
    if not isinstance(body, list) or not all(isinstance(entry, dict) for entry in body):
        raise PlanFileError(f"journal file {path} must contain a JSON array of entries")
    return body


def cleanup_from_journal(
    journal_path: Path,
    client: GatewayClient,
    *,
    confirm: Callable[[str], str] = input,
    output: Output = print,
) -> int:
    """Delete successfully created entities in reverse order."""

    entries = _load_journal(journal_path)
    created = [
        entry
        for entry in reversed(entries)
        if entry.get("method") == "POST"
        and entry.get("status") == "succeeded"
        and entry.get("id") is not None
        and isinstance(entry.get("path"), str)
    ]
    if not client.dry_run:
        answer = confirm(
            f"Type CLEANUP to delete {len(created)} entities recorded in {journal_path}: "
        )
        if answer != "CLEANUP":
            raise CleanupCancelled(
                "cleanup cancelled; confirmation did not match CLEANUP"
            )

    deleted = 0
    for entry in created:
        delete_path = f"{str(entry['path']).rstrip('/')}/{entry['id']}"
        client.write("DELETE", delete_path)
        deleted += 1
    output(
        f"{'Would delete' if client.dry_run else 'Deleted'} {deleted} created entities "
        "in reverse order."
    )
    return deleted


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build an Itero scorecard from a JSON plan (dry-run by default)."
    )
    parser.add_argument("plan", nargs="?", type=Path, help="scorecard plan JSON")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="validate only; no credentials or network",
    )
    parser.add_argument("--tenant", help="use ITERO_API_KEY_<TENANT>")
    parser.add_argument("--live", action="store_true", help="execute writes")
    parser.add_argument(
        "--force-new", action="store_true", help="replace an existing build journal"
    )
    parser.add_argument(
        "--cleanup", type=Path, metavar="JOURNAL", help="clean up a previous build"
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    transport: Transport | None = None,
    output: Output = print,
) -> int:
    args = build_parser().parse_args(argv)
    if args.cleanup is not None:
        if args.plan is not None or args.validate or args.force_new:
            raise PlanFileError(
                "--cleanup cannot be combined with a plan, --validate, or --force-new"
            )
        client = GatewayClient.from_environment(
            args.tenant, dry_run=not args.live, transport=transport, output=output
        )
        cleanup_from_journal(args.cleanup, client, output=output)
        return 0

    if args.plan is None:
        raise PlanFileError("a scorecard plan JSON path is required")
    plan = load_plan(args.plan)
    if args.validate:
        output(f"Valid scorecard plan: {args.plan}")
        return 0

    client = GatewayClient.from_environment(
        args.tenant, dry_run=not args.live, transport=transport, output=output
    )
    result = build_scorecard(
        plan,
        client,
        journal_path_for(args.plan),
        force_new=args.force_new,
        output=output,
    )
    output(
        f"Scorecard {result.template_id}: {result.category_count} categories, "
        f"{result.criterion_count} criteria, published={result.published}."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ScorecardError as exc:
        print(f"Error: {exc}", file=os.sys.stderr)
        raise SystemExit(1) from exc
