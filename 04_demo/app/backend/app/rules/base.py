from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DecisionInput:
    case_title: str
    evidence: dict[str, dict]
    evidence_statuses: dict[str, str]


@dataclass
class DecisionOutput:
    recommendation: str
    evidence_lines: list[str]
    uncertainty: str
    next_step: str
    confidence_label: str
    warnings: list[str] = field(default_factory=list)
