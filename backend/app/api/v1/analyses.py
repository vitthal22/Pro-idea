"""Analysis API endpoints.

HTTP only: parse the request, delegate to ``AnalysisService``, shape the
response. ``POST`` returns immediately (202) — the pipeline runs in the
background and the client polls ``/{id}/status`` or fetches ``/{id}``.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_analysis_service, get_current_user
from app.api.schemas.analyses import (
    AnalysisCreatedResponse,
    AnalysisCreateRequest,
    AnalysisDetailResponse,
    AnalysisListItemResponse,
    AnalysisListResponse,
    AnalysisResultPayload,
    AnalysisStatusResponse,
)
from app.models.analysis import AnalysisResultModel
from app.services.analysis import AnalysisService
from app.services.user_repository import User

router = APIRouter(prefix="/analyses", tags=["analyses"])


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
        evaluator_summaries=report.get("evaluator_summaries", {}),
        failed_evaluators=report.get("failed_evaluators", []),
        roast_fallback_used=bool(report.get("roast_fallback_used", False)),
    )


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
        result=_result_payload(analysis.result),
    )
