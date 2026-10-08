from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models import User, Report, ExpertReview
from backend.schemas import ExpertReviewCreate, ExpertReviewResponse, ReportResponse
from backend.auth import require_role, get_current_user
from backend.routers.report_routes import format_report_response

router = APIRouter(tags=["Expert Review"])


@router.post("/reports/{report_id}/review", response_model=ExpertReviewResponse)
def submit_expert_review(
    report_id: int,
    review_data: ExpertReviewCreate,
    current_user: User = Depends(require_role("expert")),
    db: Session = Depends(get_db)
):
    """Allows an agricultural expert to review a diagnosis report."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    review = ExpertReview(
        report_id=report.id,
        expert_id=current_user.id,
        verdict=review_data.verdict,
        comment=review_data.comment.strip()
    )
    db.add(review)
    db.commit()
    db.refresh(review)

    return ExpertReviewResponse(
        id=review.id,
        report_id=review.report_id,
        expert_id=review.expert_id,
        expert_name=current_user.name,
        verdict=review.verdict,
        comment=review.comment,
        created_at=review.created_at
    )


@router.get("/expert/reports", response_model=List[ReportResponse])
def get_expert_review_queue(
    current_user: User = Depends(require_role("expert")),
    db: Session = Depends(get_db)
):
    """Lists reports for expert verification, prioritizing low certainty cases."""
    reports = db.query(Report).order_by(
        desc(Report.created_at)
    ).all()
    return [format_report_response(r) for r in reports]
