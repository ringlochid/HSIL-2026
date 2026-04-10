from __future__ import annotations

from app.rules.base import DecisionOutput
from app.schemas.draft import DraftPayload


class DraftRenderService:
    def __init__(self, draft_chain) -> None:
        self.draft_chain = draft_chain

    def render(self, case_title: str, decision: DecisionOutput) -> DraftPayload:
        payload = {
            'case_title': case_title,
            'recommendation': decision.recommendation,
            'evidence_summary': ' '.join(decision.evidence_lines),
            'uncertainty': decision.uncertainty,
            'next_step': decision.next_step,
        }
        rewritten = self.draft_chain.invoke(payload) if self.draft_chain is not None else payload
        return DraftPayload.model_validate(rewritten)
