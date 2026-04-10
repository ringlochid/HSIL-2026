from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class ReportRecord(Base):
    __tablename__ = "reports"

    report_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    extraction_status: Mapped[str] = mapped_column(String(32))
    report_data: Mapped[dict] = mapped_column(JSON)
    review_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class RunRecord(Base):
    __tablename__ = "report_runs"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    patient_id: Mapped[str] = mapped_column(String(64), index=True)
    report_ids: Mapped[list[str]] = mapped_column(JSON)
    run_status: Mapped[str] = mapped_column(String(32), default="completed")
    review_status: Mapped[str] = mapped_column(String(32), default="pending_review")
    report_payload: Mapped[dict] = mapped_column(JSON)
    evidence: Mapped[list[dict]] = mapped_column(JSON)
    warnings: Mapped[list[str]] = mapped_column(JSON)
    review_note: Mapped[str | None] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_pdf_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


def build_engine(database_url: str):
    kwargs: dict[str, object] = {"future": True}
    if database_url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **kwargs)


def build_session_factory(database_url: str):
    engine = build_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True
    )


@contextmanager
def session_scope(session_factory):
    session: Session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def ping_database(session_factory) -> bool:
    with session_scope(session_factory) as session:
        session.execute(text("SELECT 1"))
    return True
