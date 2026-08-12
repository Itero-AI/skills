#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pydantic>=2.7,<3",
#     "pytest>=8.2,<9",
#     "python-dotenv>=1.0,<2",
#     "requests>=2.31,<3",
# ]
# ///
"""Tests for build_scorecard.py.

Run directly with:
    uv run skills/scorecards/scripts/test_build_scorecard.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import build_scorecard as builder
import pytest


def plan_data(*, explicit_agents: bool = True, publish: bool = True) -> dict[str, Any]:
    data: dict[str, Any] = {
        "name": "Discovery scorecard",
        "callTypes": [0, 2],
        "interactionType": 0,
        "userGroupIds": [41, 42],
        "categories": [
            {
                "name": "Discovery",
                "weight": 500,
                "scorecardType": 0,
                "criteria": [
                    {
                        "title": "Finds the business problem",
                        "criteria": "The rep identifies a concrete business problem.",
                        "rubrics": [
                            {
                                "scale": 4,
                                "description": "Finds and quantifies the problem.",
                            }
                        ],
                    }
                ],
            }
        ],
        "publish": publish,
    }
    if explicit_agents:
        data["qualitiveAgentId"] = 11
        data["qaAgentId"] = 12
    return data


def parsed_plan(
    *, explicit_agents: bool = True, publish: bool = True
) -> builder.ScorecardPlan:
    return builder.ScorecardPlan.model_validate(
        plan_data(explicit_agents=explicit_agents, publish=publish)
    )


class FakeTransport:
    """State-aware transport that returns IDs used by the next chain stage."""

    def __init__(self, fail_stage: str | None = None) -> None:
        self.fail_stage = fail_stage
        self.calls: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        path = urlsplit(url).path
        call = {"method": method, "path": path, **kwargs}
        self.calls.append(call)
        stage = self._stage(method, path)
        if self.fail_stage is not None and stage == self.fail_stage:
            raise RuntimeError(f"injected {stage} failure")
        if method == "GET" and path == builder.AGENT_PATH:
            return [
                {
                    "id": 11,
                    "name": "Qualitative Coaching",
                    "agentType": 0,
                    "interactionType": 0,
                },
                {
                    "id": 12,
                    "name": "QA Evaluation",
                    "agentType": 4,
                    "interactionType": 0,
                },
            ]
        if method == "POST" and path == builder.SCORECARD_PATH:
            return {"id": 101}
        if method == "POST" and path == builder.CATEGORY_PATH:
            return {"id": 201}
        if method == "POST" and path == builder.CRITERION_PATH:
            return {"id": 301}
        if method == "GET" and path == builder.RUBRICS_PATH:
            return [
                {
                    "id": 400 + scale,
                    "rubrikScale": scale,
                    "scorecardTemplateCriteriaId": 301,
                }
                for scale in range(6)
            ]
        return {}

    @staticmethod
    def _stage(method: str, path: str) -> str | None:
        if method == "POST" and path == builder.SCORECARD_PATH:
            return "template"
        if method == "POST" and path == builder.CATEGORY_PATH:
            return "category"
        if method == "POST" and path == builder.CRITERION_PATH:
            return "criterion"
        if method == "PUT" and path == builder.RUBRIC_PATH:
            return "rubric"
        if method == "PATCH" and path.endswith("/status"):
            return "publish"
        return None


class ExplodingTransport:
    def __init__(self) -> None:
        self.calls = 0

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        self.calls += 1
        raise AssertionError(f"transport touched: {method} {url} {kwargs}")


def live_client(
    transport: FakeTransport, output: list[str] | None = None
) -> builder.GatewayClient:
    sink = output if output is not None else []
    return builder.GatewayClient(
        "test-key",
        dry_run=False,
        transport=transport,
        output=sink.append,
    )


def test_full_chain_propagates_ids_and_publishes_last(tmp_path: Path) -> None:
    transport = FakeTransport()
    journal_path = tmp_path / "plan.json.journal.json"

    result = builder.build_scorecard(
        parsed_plan(), live_client(transport), journal_path, output=lambda _: None
    )

    assert result.model_dump() == {
        "template_id": 101,
        "category_count": 1,
        "criterion_count": 1,
        "published": True,
        "journal_path": journal_path,
    }
    calls = transport.calls
    assert [(call["method"], call["path"]) for call in calls] == [
        ("POST", builder.SCORECARD_PATH),
        ("POST", builder.CATEGORY_PATH),
        ("POST", builder.CRITERION_PATH),
        ("GET", builder.RUBRICS_PATH),
        ("PUT", builder.RUBRIC_PATH),
        ("PATCH", f"{builder.SCORECARD_PATH}/101/status"),
    ]
    assert calls[0]["json"]["qualitiveAgentId"] == 11
    assert calls[0]["json"]["qaAgentId"] == 12
    assert calls[1]["json"]["scorecardTemplateId"] == 101
    assert calls[2]["json"]["scorecardTemplateCategoryId"] == 201
    assert calls[3]["params"] == {"criteriaId": 301}
    assert calls[4]["json"] == {
        "id": 404,
        "description": "Finds and quantifies the problem.",
    }
    assert calls[-1]["json"] == {"status": 1}

    journal = json.loads(journal_path.read_text())
    assert [entry["step"] for entry in journal] == [
        "template",
        "category",
        "criterion",
        "rubric",
        "publish",
    ]
    assert [entry["id"] for entry in journal] == [101, 201, 301, 404, 101]
    assert all(entry["status"] == "succeeded" for entry in journal)


@pytest.mark.parametrize(
    ("failed_stage", "expected_steps", "successful_ids"),
    [
        ("template", ["template"], []),
        ("category", ["template", "category"], [101]),
        ("criterion", ["template", "category", "criterion"], [101, 201]),
        (
            "rubric",
            ["template", "category", "criterion", "rubric"],
            [101, 201, 301],
        ),
        (
            "publish",
            ["template", "category", "criterion", "rubric", "publish"],
            [101, 201, 301, 404],
        ),
    ],
)
def test_failure_at_each_stage_stops_and_preserves_journal(
    tmp_path: Path,
    failed_stage: str,
    expected_steps: list[str],
    successful_ids: list[int],
) -> None:
    transport = FakeTransport(fail_stage=failed_stage)
    journal_path = tmp_path / f"{failed_stage}.journal.json"
    output: list[str] = []

    with pytest.raises(builder.ApiError, match="could not reach the gateway"):
        builder.build_scorecard(
            parsed_plan(),
            live_client(transport),
            journal_path,
            output=output.append,
        )

    journal = json.loads(journal_path.read_text())
    assert [entry["step"] for entry in journal] == expected_steps
    assert [entry["id"] for entry in journal[:-1]] == successful_ids
    assert all(entry["status"] == "succeeded" for entry in journal[:-1])
    assert journal[-1]["status"] == "unconfirmed"
    assert "id" not in journal[-1]
    assert output[0] == "Build failed. Journal follows:"
    assert json.loads(output[1]) == journal
    assert (
        sum(
            FakeTransport._stage(call["method"], call["path"]) == failed_stage
            for call in transport.calls
        )
        == 1
    )
    failed_call_index = next(
        index
        for index, call in enumerate(transport.calls)
        if FakeTransport._stage(call["method"], call["path"]) == failed_stage
    )
    assert failed_call_index == len(transport.calls) - 1


def test_omitted_agents_are_resolved_from_gateway_catalog(tmp_path: Path) -> None:
    transport = FakeTransport()

    builder.build_scorecard(
        parsed_plan(explicit_agents=False, publish=False),
        live_client(transport),
        tmp_path / "agents.journal.json",
        output=lambda _: None,
    )

    assert (transport.calls[0]["method"], transport.calls[0]["path"]) == (
        "GET",
        builder.AGENT_PATH,
    )
    template_call = next(
        call
        for call in transport.calls
        if call["method"] == "POST" and call["path"] == builder.SCORECARD_PATH
    )
    assert template_call["json"]["qualitiveAgentId"] == 11
    assert template_call["json"]["qaAgentId"] == 12


def test_explicit_agent_ids_win_without_catalog_request(tmp_path: Path) -> None:
    transport = FakeTransport()

    builder.build_scorecard(
        parsed_plan(),
        live_client(transport),
        tmp_path / "explicit.journal.json",
        output=lambda _: None,
    )

    assert not any(call["path"] == builder.AGENT_PATH for call in transport.calls)


def test_validate_is_offline_and_does_not_initialize_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan_data()), encoding="utf-8")
    transport = ExplodingTransport()

    def fail_client_init(*args: Any, **kwargs: Any) -> None:
        raise AssertionError(f"client initialized: {args} {kwargs}")

    def fail_dotenv(*args: Any, **kwargs: Any) -> None:
        raise AssertionError(f"dotenv loaded: {args} {kwargs}")

    monkeypatch.setattr(builder.GatewayClient, "from_environment", fail_client_init)
    monkeypatch.setattr(builder, "load_dotenv", fail_dotenv)

    assert builder.main(["--validate", str(plan_path)], transport=transport) == 0
    assert transport.calls == 0


def test_dry_run_allows_get_but_never_touches_transport_for_writes(
    tmp_path: Path,
) -> None:
    transport = FakeTransport()
    client = builder.GatewayClient(
        "test-key", dry_run=True, transport=transport, output=lambda _: None
    )
    journal_path = tmp_path / "dry-run.journal.json"

    result = builder.build_scorecard(
        parsed_plan(explicit_agents=False),
        client,
        journal_path,
        output=lambda _: None,
    )

    assert str(result.template_id).startswith("DRY-RUN-")
    assert [(call["method"], call["path"]) for call in transport.calls] == [
        ("GET", builder.AGENT_PATH)
    ]
    assert not any(call["method"] in builder.WRITE_METHODS for call in transport.calls)
    assert not journal_path.exists()


def test_existing_journal_refuses_rerun_without_force_new(tmp_path: Path) -> None:
    journal_path = tmp_path / "existing.journal.json"
    journal_path.write_text("[]\n", encoding="utf-8")
    transport = FakeTransport()

    with pytest.raises(builder.JournalError, match="journal already exists"):
        builder.build_scorecard(
            parsed_plan(), live_client(transport), journal_path, output=lambda _: None
        )

    assert transport.calls == []


def test_cleanup_deletes_created_entities_in_reverse_order(tmp_path: Path) -> None:
    journal_path = tmp_path / "cleanup.journal.json"
    journal_path.write_text(
        json.dumps(
            [
                {
                    "step": "template",
                    "method": "POST",
                    "path": builder.SCORECARD_PATH,
                    "name": "Template",
                    "status": "succeeded",
                    "id": 101,
                },
                {
                    "step": "category",
                    "method": "POST",
                    "path": builder.CATEGORY_PATH,
                    "name": "Category",
                    "status": "succeeded",
                    "id": 201,
                },
                {
                    "step": "criterion",
                    "method": "POST",
                    "path": builder.CRITERION_PATH,
                    "name": "Criterion",
                    "status": "succeeded",
                    "id": 301,
                },
                {
                    "step": "rubric",
                    "method": "PUT",
                    "path": builder.RUBRIC_PATH,
                    "name": "Rubric",
                    "status": "succeeded",
                    "id": 404,
                },
            ]
        ),
        encoding="utf-8",
    )
    transport = FakeTransport()

    count = builder.cleanup_from_journal(
        journal_path,
        live_client(transport),
        confirm=lambda _: "CLEANUP",
        output=lambda _: None,
    )

    assert count == 3
    assert [(call["method"], call["path"]) for call in transport.calls] == [
        ("DELETE", f"{builder.CRITERION_PATH}/301"),
        ("DELETE", f"{builder.CATEGORY_PATH}/201"),
        ("DELETE", f"{builder.SCORECARD_PATH}/101"),
    ]


def test_plan_rejects_invalid_enums_and_unknown_fields() -> None:
    invalid_enum = plan_data()
    invalid_enum["interactionType"] = 2
    with pytest.raises(builder.ValidationError):
        builder.ScorecardPlan.model_validate(invalid_enum)

    unknown_field = plan_data()
    unknown_field["unexpected"] = True
    with pytest.raises(builder.ValidationError, match="Extra inputs are not permitted"):
        builder.ScorecardPlan.model_validate(unknown_field)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
