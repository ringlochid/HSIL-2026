from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status

from app.rules.base import DecisionInput
from app.schemas.draft import DraftPayload
from app.schemas.run import BatchRunRequest, BatchRunResponse, EvidenceSourceSummary, RunRequest, RunResponse, RunStatus


class WorkflowService:
    def __init__(self, reports_repo, run_repo, tool_registry, rule_engine, draft_render_service) -> None:
        self.reports_repo = reports_repo
        self.run_repo = run_repo
        self.tool_registry = tool_registry
        self.rule_engine = rule_engine
        self.draft_render_service = draft_render_service

    def run_report(self, report_id: str, _: RunRequest, batch_id: str | None = None) -> RunResponse:
        report = self.reports_repo.get(report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Report not found.')

        run_id = self.run_repo.create_run(report_id, batch_id=batch_id)
        self.run_repo.append_event(run_id, 'load_report', 'Loaded extracted report data.')

        if report.extraction_status == 'blocked':
            warning_message = 'Patient report extraction is blocked until a real parser / AI extractor is configured.'
            draft = DraftPayload(
                case_title=report.filename,
                recommendation='Interpretation blocked. A patient report was uploaded without a configured extraction model.',
                evidence_summary='No evidence collection was attempted because patient extraction is unavailable in fixture-only mode.',
                uncertainty='No patient-specific extraction was performed, so no clinical interpretation can be generated safely.',
                next_step='Configure a real parser / AI extraction path, then rerun this patient report.',
            )
            response = RunResponse(
                run_id=run_id,
                report_id=report_id,
                batch_id=batch_id,
                status=RunStatus.blocked,
                draft=draft,
                evidence=[],
                warnings=[warning_message, *report.extraction_warnings],
            )
            self.run_repo.finalize(run_id, response)
            self.run_repo.append_event(run_id, 'blocked', warning_message)
            return response

        evidence_results = []
        evidence_map = {}
        evidence_statuses = {}
        warnings: list[str] = []

        for name in ('vep', 'spliceai', 'clinvar', 'franklin'):
            tool = self.tool_registry[name]
            self.run_repo.append_event(run_id, f'{name}_start', f'Collecting {name} evidence.')
            result = tool.get_evidence()
            evidence_results.append(
                EvidenceSourceSummary(
                    source=result.source,
                    status=result.status,
                    request_identity=result.request_identity,
                    summary=result.summary,
                    warnings=result.warnings,
                )
            )
            evidence_map[name] = result.summary
            evidence_statuses[name] = result.status
            warnings.extend(result.warnings)
            self.run_repo.append_event(run_id, f'{name}_complete', f'{name} evidence status: {result.status}.')

        case_title = report.extracted_case.report_title
        decision = self.rule_engine.evaluate(
            DecisionInput(case_title=case_title, evidence=evidence_map, evidence_statuses=evidence_statuses)
        )
        warnings.extend(decision.warnings)
        draft = self.draft_render_service.render(case_title, decision)
        response = RunResponse(
            run_id=run_id,
            report_id=report_id,
            batch_id=batch_id,
            status=RunStatus.degraded if warnings else RunStatus.completed,
            draft=draft,
            evidence=evidence_results,
            warnings=warnings,
        )
        self.run_repo.finalize(run_id, response)
        self.run_repo.append_event(run_id, 'draft_complete', 'Draft generated successfully.')
        return response

    def run_batch(self, payload: BatchRunRequest) -> BatchRunResponse:
        reports = [self.reports_repo.get(report_id) for report_id in payload.report_ids]
        missing = [report_id for report_id, report in zip(payload.report_ids, reports) if report is None]
        if missing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Reports not found: {", ".join(missing)}')

        batch_id = f'batch_{uuid4().hex[:12]}'
        results = [self.run_report(report_id, RunRequest(force_refresh=payload.force_refresh), batch_id=batch_id) for report_id in payload.report_ids]
        warnings = [
            f'{result.report_id}: {warning}'
            for result in results
            for warning in result.warnings
        ]
        return BatchRunResponse(batch_id=batch_id, mode=payload.mode, results=results, warnings=warnings)
