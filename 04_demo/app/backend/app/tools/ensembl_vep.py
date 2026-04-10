from __future__ import annotations

from collections import Counter

import httpx

from app.tools.base import FixtureBackedTool, ToolResult


class EnsemblVepTool(FixtureBackedTool):
    source = "vep"
    fixture_name = "vep_fixtures.json"
    HGVS = "NM_000329.3:c.260A>G"

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
            f"{self.settings.vep_base_url}/vep/human/hgvs/{self.HGVS}",
            params={"content-type": "application/json"},
            headers={"Accept": "application/json"},
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()[0]
        consequences = payload.get("transcript_consequences", [])
        canonical = next(
            item
            for item in consequences
            if item.get("gene_symbol") == "RPE65"
            and item.get("cds_start") == 260
            and item.get("protein_start") == 87
        )
        term_counter = Counter(
            term for item in consequences for term in item.get("consequence_terms", [])
        )
        total_terms = sum(term_counter.values()) or 1
        distribution = {
            key: round((count / total_terms) * 100, 1) for key, count in term_counter.items()
        }
        summary = {
            "gene": canonical.get("gene_symbol"),
            "transcript_id": canonical.get("transcript_id"),
            "biotype": canonical.get("biotype"),
            "protein_change": canonical.get("amino_acids"),
            "cds_position": canonical.get("cds_start"),
            "protein_position": canonical.get("protein_start"),
            "most_severe_consequence": payload.get("most_severe_consequence"),
            "consequence_distribution": distribution,
        }
        return ToolResult(
            source=self.source,
            status="live",
            request_identity={"hgvs": self.HGVS},
            summary=summary,
            raw=payload,
        )
