from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.client import build_extraction_chain, build_search_answer_chain
from app.api.routes import build_api_router
from app.core.config import ensure_runtime_dirs, get_settings
from app.core.db import build_session_factory, initialize_database
from app.core.logging import configure_logging, get_logger
from app.repos.reports_repo import ReportsRepo
from app.repos.run_repo import RunRepo
from app.repos.search_repo import SearchRepo
from app.rules.clinic_rules import ClinicRules
from app.services.final_report import FinalReportService
from app.services.intake import IntakeService
from app.services.recommendation import RecommendationService
from app.services.search import SearchService
from app.services.search_answer import SearchAnswerService
from app.services.search_index import SearchIndexService
from app.services.workflow import WorkflowService
from app.tools.registry import build_tool_registry
from app.tools.report_pdf import ReportPdfTool

logger = get_logger(__name__)


def create_app(settings=None) -> FastAPI:
    settings = settings or get_settings()
    ensure_runtime_dirs(settings)
    configure_logging(settings.debug)
    db_session_factory = build_session_factory(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        initialize_database(db_session_factory)
        logger.info("HSIL demo backend ready at %s:%s", settings.host, settings.port)
        yield

    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    reports_repo = ReportsRepo(db_session_factory)
    run_repo = RunRepo(db_session_factory)
    search_repo = SearchRepo(db_session_factory)
    report_pdf_tool = ReportPdfTool()
    extraction_chain = build_extraction_chain(settings)
    search_answer_chain = build_search_answer_chain(settings)
    tool_registry = build_tool_registry(settings)
    search_index_service = SearchIndexService(search_repo, reports_repo, run_repo)
    search_service = SearchService(search_repo)

    app.state.settings = settings
    app.state.db_session_factory = db_session_factory
    app.state.reports_repo = reports_repo
    app.state.run_repo = run_repo
    app.state.search_repo = search_repo
    app.state.search_index_service = search_index_service
    app.state.search_service = search_service
    app.state.search_answer_service = SearchAnswerService(
        settings=settings,
        search_service=search_service,
        answer_chain=search_answer_chain,
    )
    app.state.intake_service = IntakeService(
        settings, reports_repo, report_pdf_tool, extraction_chain, search_index_service
    )
    app.state.workflow_service = WorkflowService(
        reports_repo=reports_repo,
        run_repo=run_repo,
        tool_registry=tool_registry,
        rule_engine=ClinicRules(),
        search_index_service=search_index_service,
    )
    app.state.recommendation_service = RecommendationService(run_repo, search_index_service)
    app.state.final_report_service = FinalReportService(
        settings, run_repo, search_index_service
    )

    app.include_router(build_api_router())
    return app


app = create_app()
