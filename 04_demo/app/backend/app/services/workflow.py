from __future__ import annotations

from fastapi import HTTPException, status

from app.rules.base import DecisionInput
from app.schemas.run import EvidenceSourceSummary, RunRequest, RunResponse, RunStatus


class WorkflowService:
    def __init__(self, reports_repo, run_repo, tool_registry, rule_engine, draft_render_service) -> None:
        self.reports_repo = reports_repo
        self.run_repo = run_repo
        self.tool_registry = tool_registry
        self.rule_engine = rule_engine
        self.draft_render_service = draft_render_service

    def run_report(self, report_id: str, _: RunRequest) -> RunResponse:
        report = self.reports_repo.get(report_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Report not found.')

        run_id = self.run_repo.create_run(report_id)
        self.run_repo.append_event(report_id, 'load_report', 'Loaded extracted report data.')

        evidence_results = []
        evidence_map = {}
        evidence_statuses = {}
        warnings: list[str] = []

        for name in ('vep', 'spliceai', 'clinvar', 'franklin'):
            tool = self.tool_registry[name]
            self.run_repo.append_event(report_id, f'{name}_start', f'Collecting {name} evidence.')
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
            self.run_repo.append_event(report_id, f'{name}_complete', f'{name} evidence status: {result.status}.')

        case_title = report.extracted_case.report_title
        decision = self.rule_engine.evaluate(
            DecisionInput(case_title=case_title, evidence=evidence_map, evidence_statuses=evidence_statuses)
        )
        warnings.extend(decision.warnings)
        draft = self.draft_render_service.render(case_title, decision)
        response = RunResponse(
            run_id=run_id,
            report_id=report_id,
            status=RunStatus.degraded if warnings else RunStatus.completed,
            draft=draft,
            evidence=evidence_results,
            warnings=warnings,
        )
        self.run_repo.finalize(report_id, response)
        self.run_repo.append_event(report_id, 'draft_complete', 'Draft generated successfully.')
        return response
