"""Resume API endpoints.

HTTP only: parse the request, delegate to ``ResumeService``, shape the
response.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, UploadFile, status

from app.api.deps import get_current_user, get_resume_service
from app.api.schemas.resumes import (
    ResumeDetailResponse,
    ResumeListResponse,
    ResumeResponse,
)
from app.services.resume import ResumeService
from app.services.user_repository import User

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=ResumeDetailResponse,
)
async def upload_resume(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeDetailResponse:
    """Upload a resume and extract its text."""
    resume = await service.upload(user_id=current_user.id, upload=file)
    return ResumeDetailResponse.model_validate(resume)


@router.get("", response_model=ResumeListResponse)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeListResponse:
    """List the current user's resumes, newest first."""
    resumes = await service.list(user_id=current_user.id)
    return ResumeListResponse(
        items=[ResumeResponse.model_validate(resume) for resume in resumes],
        total=len(resumes),
    )


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> ResumeDetailResponse:
    """Return one resume owned by the current user."""
    resume = await service.get(user_id=current_user.id, resume_id=resume_id)
    return ResumeDetailResponse.model_validate(resume)


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    service: ResumeService = Depends(get_resume_service),
) -> Response:
    """Soft-delete a resume and remove its stored file."""
    await service.delete(user_id=current_user.id, resume_id=resume_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
