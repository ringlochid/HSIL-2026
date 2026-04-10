from __future__ import annotations

import httpx

from app.tools.base import FixtureBackedTool, ToolResult


class ClinvarTool(FixtureBackedTool):
    source = "clinvar"
    fixture_name = "clinvar_fixtures.json"
    CLINVAR_ID = "1421454"

    def get_evidence(self) -> ToolResult:
        if not self.settings.use_real_apis:
            fixture = self.load_fixture()
            return ToolResult(source=self.source, status="fixture", **fixture)
        try:
            return self._fetch_live()
        except Exception as exc:
            fixture = self.load_fixture()
            return ToolResult(
                source=self.source,
                status="fallback",
                warnings=[f"live_fetch_failed:{type(exc).__name__}"],
                **fixture,
            )

    def _fetch_live(self) -> ToolResult:
        response = httpx.get(
            f"{self.settings.clinvar_base_url}/esummary.fcgi",
            params={"db": "clinvar", "id": self.CLINVAR_ID, "retmode": "json"},
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()["result"][self.CLINVAR_ID]
        summary = {
            "gene": payload["genes"][0]["symbol"],
            "protein_change": payload.get("protein_change"),
            "classification": payload["germline_classification"]["description"],
            "review_status": payload["germline_classification"]["review_status"],
            "conditions": [
                item["trait_name"] for item in payload["germline_classification"]["trait_set"]
            ],
            "consequence": (payload.get("molecular_consequence_list") or [""])[0],
            "accession": payload.get("accession"),
        }
        return ToolResult(
            source=self.source,
            status="live",
            request_identity={"clinvar_id": self.CLINVAR_ID},
            summary=summary,
            raw=payload,
        )
