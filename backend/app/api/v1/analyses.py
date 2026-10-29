"""Analysis API endpoints.

HTTP only: parse the request, delegate to ``AnalysisService``, shape the
response. ``POST`` returns immediately (202) — the pipeline runs in the
background; clients watch via the SSE stream, poll ``/{id}/status``, or
fetch ``/{id}``.
"""

import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.scoring import score_verdict
from app.api.deps import get_analysis_service, get_current_user, get_db
from app.api.schemas.analyses import (
    AnalysisCreatedResponse,
    AnalysisCreateRequest,
    AnalysisDetailResponse,
    AnalysisListItemResponse,
    AnalysisListResponse,
    AnalysisResultPayload,
    AnalysisStatusResponse,
    ScoreVerdict,
)
from app.models.analysis import AnalysisModel, AnalysisResultModel
from app.services.analysis import AnalysisService
from app.services.user_repository import User

router = APIRouter(prefix="/analyses", tags=["analyses"])

# SSE stream pacing (seconds) — status poll + proxy-defeating heartbeat.
_STREAM_POLL_SECONDS = 1.0
_STREAM_HEARTBEAT_SECONDS = 15.0
_TERMINAL_STATUSES = {"completed", "partial", "failed"}


def _result_payload(result: AnalysisResultModel | None) -> AnalysisResultPayload | None:
    if result is None:
        return None
    report = result.final_report or {}
    return AnalysisResultPayload(
        overall_score=float(result.overall_score)
        if result.overall_score is not None
        else None,
        critical_issues=result.critical_issues or [],
        warnings=result.warnings or [],
        suggestions=result.suggestions or [],
        positive_notes=result.positive_notes or [],
        final_roast=result.final_roast,
        breakdown=result.scoring_breakdown,
        methodology=result.scoring_methodology,
        job_match_feedback=result.job_match_feedback,
        reality_check=report.get("reality_check"),
        evaluator_summaries=report.get("evaluator_summaries", {}),
        failed_evaluators=report.get("failed_evaluators", []),
        roast_fallback_used=bool(report.get("roast_fallback_used", False)),
    )


def _sse_event(event: str, data: dict[str, object]) -> str:
    """One SSE frame in the ARCHITECTURE §10 wire format."""
    frame_data = json.dumps(data)
    return f"event: {event}\ndata: {frame_data}\n\n"


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AnalysisCreatedResponse,
)
async def create_analysis(
    payload: AnalysisCreateRequest,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisCreatedResponse:
    """Queue a roast; the pipeline runs in the background."""
    analysis = await service.create_analysis(
        user_id=current_user.id,
        resume_id=payload.resume_id,
        analysis_type=payload.analysis_type,
        target_role=payload.target_role,
        job_description=payload.job_description,
        custom_instructions=payload.custom_instructions,
        tier=current_user.tier,
    )
    return AnalysisCreatedResponse(analysis_id=analysis.id, status=analysis.status)


@router.get("", response_model=AnalysisListResponse)
async def list_analyses(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisListResponse:
    """The current user's analyses, newest first."""
    analyses, total = await service.list_analyses(
        user_id=current_user.id, limit=limit, offset=offset
    )
    return AnalysisListResponse(
        items=[
            AnalysisListItemResponse(
                id=analysis.id,
                resume_id=analysis.resume_id,
                analysis_type=analysis.analysis_type,
                status=analysis.status,
                created_at=analysis.created_at,
                overall_score=float(analysis.result.overall_score)
                if analysis.result is not None
                and analysis.result.overall_score is not None
                else None,
            )
            for analysis in analyses
        ],
        total=total,
    )


@router.get("/{analysis_id}/stream")
async def stream_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
    service: AnalysisService = Depends(get_analysis_service),
) -> StreamingResponse:
    """SSE viewer of the pipeline (ARCHITECTURE §10).

    The stream is a viewer, never the executor: the pipeline keeps running
    whether or not anyone connects, and a stream opened after completion
    immediately replays the terminal event (idempotent).
    """
    # Ownership check before the stream opens (404, not an error event).
    await service.get_analysis(user_id=current_user.id, analysis_id=analysis_id)

    async def event_stream() -> AsyncIterator[str]:
        last_status: str | None = None
        since_heartbeat = 0.0
        while True:
            analysis = await session.scalar(
                select(AnalysisModel)
                .options(selectinload(AnalysisModel.result))
                .where(AnalysisModel.id == analysis_id)
            )
            if analysis is None:
                yield _sse_event(
                    "error",
                    {"code": "NOT_FOUND", "message": "Analysis not found"},
                )
                return
            status_value = analysis.status
            if status_value != last_status:
                last_status = status_value
                if status_value in _TERMINAL_STATUSES:
                    if status_value == "failed":
                        yield _sse_event(
                            "error",
                            {
                                "code": "ANALYSIS_FAILED",
                                "message": analysis.error_message
                                or "The pipeline failed.",
                            },
                        )
                    else:
                        yield _sse_event(
                            "complete",
                            {
                                "analysis_id": str(analysis.id),
                                "status": status_value,
                                "overall_score": (
                                    float(analysis.result.overall_score)
                                    if analysis.result
                                    and analysis.result.overall_score is not None
                                    else None
                                ),
                            },
                        )
                    return
                yield _sse_event("status", {"step": status_value, "state": "running"})
            since_heartbeat += _STREAM_POLL_SECONDS
            if since_heartbeat >= _STREAM_HEARTBEAT_SECONDS:
                since_heartbeat = 0.0
                yield ": heartbeat\n\n"
            await asyncio.sleep(_STREAM_POLL_SECONDS)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisStatusResponse:
    """Lightweight poll: status and error message only."""
    analysis = await service.get_analysis(
        user_id=current_user.id, analysis_id=analysis_id
    )
    return AnalysisStatusResponse.model_validate(analysis)


@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis(
    analysis_id: UUID,
    current_user: User = Depends(get_current_user),
    service: AnalysisService = Depends(get_analysis_service),
) -> AnalysisDetailResponse:
    """Full analysis record, including the roast when finished."""
    analysis = await service.get_analysis(
        user_id=current_user.id, analysis_id=analysis_id
    )
    return AnalysisDetailResponse(
        id=analysis.id,
        resume_id=analysis.resume_id,
        analysis_type=analysis.analysis_type,
        status=analysis.status,
        error_message=analysis.error_message,
        created_at=analysis.created_at,
        completed_at=analysis.completed_at,
        processing_time_ms=analysis.processing_time_ms,
        score_verdict=(
            ScoreVerdict(
                **score_verdict(
                    float(analysis.result.overall_score)
                    if analysis.result is not None
                    and analysis.result.overall_score is not None
                    else 0.0
                )
            )
            if analysis.result is not None and analysis.result.overall_score is not None
            else None
        ),
        result=_result_payload(analysis.result),
    )
