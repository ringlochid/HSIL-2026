from __future__ import annotations

import httpx

from app.tools.base import FixtureBackedTool, ToolResult


class FranklinTool(FixtureBackedTool):
    source = 'franklin'
    fixture_name = 'franklin_fixtures.json'
    SEARCH_TEXT = 'RPE65:c.260A>G'

    def get_evidence(self) -> ToolResult:
        if not self.settings.use_real_apis:
            fixture = self.load_fixture()
            return ToolResult(source=self.source, status='fixture', **fixture)
        if not self.settings.franklin_api_token:
            fixture = self.load_fixture()
            return ToolResult(
                source=self.source,
                status='fallback',
                request_identity=fixture['request_identity'],
                summary=fixture['summary'],
                warnings=['franklin_auth_unavailable'],
                raw=None,
            )
        try:
            return self._fetch_live()
        except Exception as exc:
            fixture = self.load_fixture()
            return ToolResult(source=self.source, status='fallback', warnings=[f'live_fetch_failed:{type(exc).__name__}'], **fixture)

    def _fetch_live(self) -> ToolResult:
        parse_response = httpx.post(
            f'{self.settings.franklin_parse_base_url}/api/parse_search',
            json={'search_text_input': self.SEARCH_TEXT},
            timeout=10.0,
        )
        parse_response.raise_for_status()
        parse_payload = parse_response.json()
        search_response = httpx.get(
            f'{self.settings.franklin_base_url}/v2/search/snp/',
            params={'search_text': self.SEARCH_TEXT},
            headers={'Authorization': f'Bearer {self.settings.franklin_api_token}'},
            timeout=10.0,
        )
        search_response.raise_for_status()
        search_payload = search_response.json()
        variant_block = parse_payload.get('best_variant_option') or parse_payload
        transcript = (
            variant_block.get('canonical_transcript')
            or variant_block.get('canonical_tanscript')
            or variant_block.get('transcript')
            or 'N/A'
        )
        summary = {
            'search_text': self.SEARCH_TEXT,
            'transcript': transcript,
            'functional_data': search_payload.get('classification', {}).get('acmg_classification', 'Unavailable')
            if isinstance(search_payload, dict)
            else 'Unavailable',
            'population_data': search_payload.get('annotations', {}).get('frequencies', {}).get('aggregated_frequency', 'Unavailable')
            if isinstance(search_payload, dict)
            else 'Unavailable',
            'in_silico_prediction': search_payload.get('annotations', {}).get('predictions', {}).get('aggregated_predictions', 'Unavailable')
            if isinstance(search_payload, dict)
            else 'Unavailable',
        }
        return ToolResult(
            source=self.source,
            status='live',
            request_identity={'search_text': self.SEARCH_TEXT},
            summary=summary,
            raw={'parse_payload': parse_payload, 'search_payload': search_payload},
        )
