"""Schema-level tests: constraints, JSONB round-trip, FK cascade."""

from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import AnalysisModel, AnalysisResultModel
from app.models.analysis_usage import AnalysisUsageModel
from app.models.resume import ResumeModel
from app.models.user import UserModel
from app.services.user_repository import PostgresUserRepository


async def _make_user(session: AsyncSession, email: str) -> UserModel:
    domain = await PostgresUserRepository(session).create(
        email=email,
        name="Schema Test",
        password_hash="hash",
    )
    user = await session.get(UserModel, domain.id)
    assert user is not None
    return user


async def _make_resume(session: AsyncSession, user_id) -> ResumeModel:
    resume = ResumeModel(
        user_id=user_id,
        file_path=f"{user_id}/{uuid4()}.pdf",
        original_name="cv.pdf",
        file_size=1234,
        mime_type="application/pdf",
    )
    session.add(resume)
    await session.flush()
    return resume


async def test_full_chain_persists_and_roundtrips(
    db_session: AsyncSession,
    email_factory,
) -> None:
    user = await _make_user(db_session, email_factory("chain"))
    resume = await _make_resume(db_session, user.id)
    resume.raw_text = "Python developer"
    resume.structured_data = {"skills": ["python"], "years": 3}

    analysis = AnalysisModel(
        user_id=user.id,
        resume_id=resume.id,
        analysis_type="general",
        status="completed",
        prompt_versions_used={"recruiter": "1.0.0"},
    )
    db_session.add(analysis)
    await db_session.flush()

    result = AnalysisResultModel(
        analysis_id=analysis.id,
        overall_score=Decimal("72.50"),
        critical_issues=[{"title": "No metrics"}],
        final_roast="Needs work.",
        final_report={"overall_score": 72.5},
    )
    usage = AnalysisUsageModel(
        user_id=user.id,
        analysis_id=analysis.id,
        ai_model="test-model",
        prompt_tokens=100,
        completion_tokens=50,
        cost_usd=Decimal("0.000123"),
    )
    db_session.add_all([result, usage])
    await db_session.commit()

    stored_resume = await db_session.get(ResumeModel, resume.id)
    assert stored_resume is not None
    assert stored_resume.parsing_status == "pending"
    assert stored_resume.structured_data == {"skills": ["python"], "years": 3}
    assert stored_resume.deleted_at is None

    stored_result = await db_session.scalar(
        select(AnalysisResultModel).where(
            AnalysisResultModel.analysis_id == analysis.id
        )
    )
    assert stored_result is not None
    assert stored_result.overall_score == Decimal("72.50")
    assert stored_result.critical_issues == [{"title": "No metrics"}]

    # Scope by analysis — the dev DB holds real usage rows from live runs.
    stored_usage = await db_session.scalar(
        select(AnalysisUsageModel).where(AnalysisUsageModel.analysis_id == analysis.id)
    )
    assert stored_usage is not None
    assert stored_usage.cost_usd == Decimal("0.000123")


async def test_one_result_per_analysis(
    db_session: AsyncSession,
    email_factory,
) -> None:
    user = await _make_user(db_session, email_factory("unique"))
    resume = await _make_resume(db_session, user.id)
    analysis = AnalysisModel(
        user_id=user.id,
        resume_id=resume.id,
        analysis_type="general",
    )
    db_session.add(analysis)
    await db_session.flush()

    db_session.add(AnalysisResultModel(analysis_id=analysis.id))
    await db_session.flush()

    with pytest.raises(IntegrityError):
        db_session.add(AnalysisResultModel(analysis_id=analysis.id))
        await db_session.flush()
    await db_session.rollback()


async def test_resume_requires_existing_user(db_session: AsyncSession) -> None:
    db_session.add(
        ResumeModel(
            user_id=uuid4(),
            file_path="missing/user.pdf",
            original_name="cv.pdf",
            file_size=1,
            mime_type="application/pdf",
        )
    )

    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


async def test_deleting_user_cascades_through_children(
    db_session: AsyncSession,
    email_factory,
) -> None:
    user = await _make_user(db_session, email_factory("cascade"))
    resume = await _make_resume(db_session, user.id)
    analysis = AnalysisModel(
        user_id=user.id,
        resume_id=resume.id,
        analysis_type="general",
    )
    db_session.add(analysis)
    await db_session.flush()
    db_session.add_all(
        [
            AnalysisResultModel(analysis_id=analysis.id),
            AnalysisUsageModel(
                user_id=user.id,
                analysis_id=analysis.id,
                ai_model="test-model",
            ),
        ]
    )
    await db_session.commit()

    # Bulk delete bypasses ORM cascades, so this proves the DB-level FKs.
    await db_session.execute(delete(UserModel).where(UserModel.id == user.id))
    await db_session.commit()

    # The dev database is shared with real data, so assert on this user's
    # rows only — every row they owned must be gone.
    owned: list[tuple[Any, Any]] = [
        (ResumeModel, ResumeModel.user_id == user.id),
        (AnalysisModel, AnalysisModel.user_id == user.id),
        (AnalysisResultModel, AnalysisResultModel.analysis_id == analysis.id),
        (AnalysisUsageModel, AnalysisUsageModel.user_id == user.id),
    ]
    for model, scope in owned:
        remaining = await db_session.scalar(
            select(func.count()).select_from(model).where(scope)
        )
        assert remaining == 0, f"{model.__tablename__} rows survived the cascade"


async def test_relationships_do_not_lazy_load(
    db_session: AsyncSession,
    email_factory,
) -> None:
    user = await _make_user(db_session, email_factory("lazy"))
    resume = await _make_resume(db_session, user.id)
    await db_session.commit()

    with pytest.raises(InvalidRequestError):
        _ = resume.user

    with pytest.raises(InvalidRequestError):
        _ = user.resumes
