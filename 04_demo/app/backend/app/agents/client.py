from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.agents.prompts import draft_prompt, extraction_prompt
from app.core.config import Settings


class MockExtractionChain:
    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path

    def invoke(self, _: dict[str, Any]) -> dict[str, Any]:
        return json.loads(self.fixture_path.read_text())


class MockDraftChain:
    def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload


def build_tool_enabled_llm(settings: Settings):
    if settings.llm_provider == 'mock' or not settings.openai_api_key:
        return None
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)


def build_extraction_chain(settings: Settings):
    model = build_tool_enabled_llm(settings)
    if model is None:
        return None

    class LiveExtractionChain:
        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            from langchain_core.prompts import ChatPromptTemplate

            prompt = ChatPromptTemplate.from_messages([
                ('system', extraction_prompt()),
                ('human', 'Filename: {filename}\nReport text:\n{report_text}'),
            ])
            chain = prompt | model.with_structured_output(dict)
            return chain.invoke(payload)

    return LiveExtractionChain()


def build_draft_chain(settings: Settings):
    model = build_tool_enabled_llm(settings)
    if model is None:
        return None

    class LiveDraftChain:
        def invoke(self, payload: dict[str, Any]) -> dict[str, Any]:
            from langchain_core.prompts import ChatPromptTemplate

            prompt = ChatPromptTemplate.from_messages([
                ('system', draft_prompt()),
                ('human', 'Recommendation: {recommendation}\nEvidence: {evidence_summary}\nUncertainty: {uncertainty}\nNext step: {next_step}'),
            ])
            chain = prompt | model.with_structured_output(dict)
            return chain.invoke(payload)

    return LiveDraftChain()
