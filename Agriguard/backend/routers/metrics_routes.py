from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database import get_db
from backend.models import ProcessingLog, Report, User
from backend.schemas import MetricsSummary

router = APIRouter(prefix="/metrics", tags=["Metrics & Observability"])


@router.get("/summary", response_model=MetricsSummary)
def get_metrics_summary(db: Session = Depends(get_db)):
    """Computes operational performance telemetry from processing_logs."""
    total_logs = db.query(func.count(ProcessingLog.id)).scalar() or 0
    successful = db.query(func.count(ProcessingLog.id)).filter(ProcessingLog.success == True).scalar() or 0
    failed = total_logs - successful

    success_rate = (successful / total_logs * 100.0) if total_logs > 0 else 100.0
    avg_duration = db.query(func.avg(ProcessingLog.duration_ms)).scalar() or 0.0

    total_reports = db.query(func.count(Report.id)).scalar() or 0
    total_users = db.query(func.count(User.id)).scalar() or 0

    return MetricsSummary(
        total_processed=total_logs,
        successful_runs=successful,
        failed_runs=failed,
        success_rate_percent=round(float(success_rate), 2),
        avg_duration_ms=round(float(avg_duration), 2),
        total_reports=total_reports,
        total_users=total_users
    )
