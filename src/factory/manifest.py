"""Manifest model for project.yaml (pydantic v2), including approval-policy validation.

The approval-policy validation is protected core: human approval for merge and for
production defaults to on (ADRs 0002, 0007), and disabling either flag requires a
waiver naming an existing accepted ADR in docs/decisions/.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


class Environment(BaseModel):
    configured: bool = False


class Environments(BaseModel):
    dev: Environment = Field(default_factory=Environment)
    prod: Environment = Field(default_factory=Environment)


class AIRole(BaseModel):
    enabled: bool = False
    model: str = ""


class AIRoles(BaseModel):
    planning: AIRole = Field(default_factory=AIRole)
    execution: AIRole = Field(default_factory=AIRole)
    review: AIRole = Field(default_factory=AIRole)


class ApprovalPolicy(BaseModel):
    human_approval_required_for_merge: bool = True
    human_approval_required_for_production: bool = True
    waiver_adr: str | None = None


class Manifest(BaseModel):
    """A project manifest as written to data/projects/<id>/project.yaml."""

    schema_version: Literal[1]
    id: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    name: str
    description: str = ""
    repository: str = ""
    stack: str = ""
    principles_version: str | None = None
    environments: Environments = Field(default_factory=Environments)
    ai_roles: AIRoles = Field(default_factory=AIRoles)
    approval_policy: ApprovalPolicy = Field(default_factory=ApprovalPolicy)

    @field_validator("name", "description", "repository", "stack")
    @classmethod
    def strip_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("name")
    @classmethod
    def name_required(cls, value: str) -> str:
        if not value:
            raise ValueError("name is required")
        return value

    @model_validator(mode="after")
    def check_approval_waiver(self) -> Manifest:
        policy = self.approval_policy
        if (
            policy.human_approval_required_for_merge
            and policy.human_approval_required_for_production
        ):
            return self
        waiver = (policy.waiver_adr or "").strip()
        if not waiver:
            raise ValueError(
                "approval policy disabled without a waiver: "
                "approval_policy.waiver_adr must name an existing accepted ADR"
            )
        if not is_accepted_adr(waiver):
            raise ValueError(
                f"waiver_adr {waiver!r} does not name an existing accepted ADR in "
                "docs/decisions/"
            )
        return self

    def roles_enabled(self) -> int:
        return sum(
            role.enabled
            for role in (
                self.ai_roles.planning,
                self.ai_roles.execution,
                self.ai_roles.review,
            )
        )


def parse_adr_ids_status() -> dict[str, str]:
    """Map ADR id -> status for files in docs/decisions/ (frontmatter only)."""
    root = Path(__file__).resolve().parents[2]
    decisions_dir = root / "docs" / "decisions"
    statuses: dict[str, str] = {}
    if not decisions_dir.is_dir():
        return statuses
    frontmatter = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
    for path in decisions_dir.glob("*.md"):
        if path.name in {"README.md", "0000-template.md"}:
            continue
        match = frontmatter.match(path.read_text(encoding="utf-8"))
        if not match:
            continue
        try:
            front = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            continue
        adr_id = str(front.get("id", "")).strip()
        if adr_id:
            statuses[adr_id] = str(front.get("status", "")).strip()
    return statuses


def is_accepted_adr(adr_id: str) -> bool:
    return parse_adr_ids_status().get(adr_id) == "accepted"


def validate_manifest(data: dict) -> Manifest | str:
    """Validate a manifest dict; return the model or an error message."""
    try:
        return Manifest.model_validate(data)
    except Exception as exc:
        return str(exc)
