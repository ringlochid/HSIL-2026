from __future__ import annotations

import httpx

from app.tools.base import FixtureBackedTool, ToolResult


class SpliceAiTool(FixtureBackedTool):
    source = 'spliceai'
    fixture_name = 'spliceai_fixtures.json'
    VARIANT = 'chr1-68444869-T-C'
    HG = 38
    DISTANCE = 500
    MASK = 0

    def get_evidence(self) -> ToolResult:
        if not self.settings.use_real_apis:
            fixture = self.load_fixture()
            return ToolResult(source=self.source, status='fixture', **fixture)
        try:
            return self._fetch_live()
        except Exception as exc:
            fixture = self.load_fixture()
            return ToolResult(source=self.source, status='fallback', warnings=[f'live_fetch_failed:{type(exc).__name__}'], **fixture)

    def _fetch_live(self) -> ToolResult:
        response = httpx.get(
            self.settings.spliceai_base_url,
            params={
                'hg': self.HG,
                'variant': self.VARIANT,
                'distance': self.DISTANCE,
                'mask': self.MASK,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        payload = response.json()
        top = payload['scores'][0]
        summary = {
            'gene': top.get('g_name'),
            'transcript_id': top.get('t_id'),
            'acceptor_loss': float(top.get('DS_AL', 0.0)),
            'donor_loss': float(top.get('DS_DL', 0.0)),
            'acceptor_gain': float(top.get('DS_AG', 0.0)),
            'donor_gain': float(top.get('DS_DG', 0.0)),
            'distance': int(payload.get('distance', self.DISTANCE)),
            'mask': int(payload.get('mask', self.MASK)),
        }
        return ToolResult(
            source=self.source,
            status='live',
            request_identity={'hg': self.HG, 'variant': self.VARIANT, 'distance': self.DISTANCE, 'mask': self.MASK},
            summary=summary,
            raw=payload,
        )
