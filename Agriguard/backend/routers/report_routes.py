import os
import time
import json
import uuid
import logging
from typing import Optional, List
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from backend.config import settings
from backend.database import get_db
from backend.models import User, Report, ProcessingLog, ExpertReview
from backend.schemas import ReportResponse, ValidationIssue, ClassPrediction, DiseaseInsight
from backend.auth import get_current_user
from backend.services.validation import validate_leaf_image, ImageValidationError
from backend.services.classifier import classifier
from backend.services.severity import analyze_leaf_severity

logger = logging.getLogger("agriguard.reports")

router = APIRouter(prefix="/reports", tags=["Reports"])

# Simple in-memory rate limiting: user_id -> list of timestamps
_upload_history = {}


def check_rate_limit(user_id: int, max_requests: int = 20, window_seconds: int = 60):
    now = time.time()
    timestamps = _upload_history.get(user_id, [])
    # Filter out timestamps older than window
    timestamps = [t for t in timestamps if now - t < window_seconds]
    if len(timestamps) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: You can scan at most {max_requests} crops per minute. Please wait."
        )
    timestamps.append(now)
    _upload_history[user_id] = timestamps


def load_knowledge_base() -> dict:
    kb_path = Path(settings.KNOWLEDGE_BASE_PATH)
    if not kb_path.exists():
        kb_path = Path("knowledge/diseases.json")
    if kb_path.exists():
        with open(kb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


_KB_CACHE = None


def get_kb() -> dict:
    global _KB_CACHE
    if _KB_CACHE is None:
        _KB_CACHE = load_knowledge_base()
    return _KB_CACHE


def format_report_response(report: Report, validation_issue: Optional[dict] = None) -> dict:
    top3_list = []
    if report.top3_json:
        try:
            top3_list = json.loads(report.top3_json)
        except Exception:
            top3_list = []

    insight_dict = None
    if report.insight_json:
        try:
            insight_dict = json.loads(report.insight_json)
        except Exception:
            insight_dict = None

    reviews_list = []
    if report.expert_reviews:
        for r in report.expert_reviews:
            reviews_list.append({
                "id": r.id,
                "expert_id": r.expert_id,
                "expert_name": r.expert.name if r.expert else "Expert",
                "verdict": r.verdict,
                "comment": r.comment,
                "created_at": r.created_at
            })

    v_issue = None
    if validation_issue:
        v_issue = validation_issue
    elif report.status == "needs_better_image" and report.notes:
        try:
            v_issue = json.loads(report.notes)
        except Exception:
            pass

    return {
        "id": report.id,
        "user_id": report.user_id,
        "image_path": report.image_path,
        "overlay_path": report.overlay_path,
        "crop": report.crop,
        "location": report.location,
        "notes": report.notes if report.status != "needs_better_image" else None,
        "predicted_class": report.predicted_class,
        "confidence": report.confidence,
        "top3": top3_list,
        "severity": report.severity,
        "severity_ratio": report.severity_ratio,
        "status": report.status,
        "validation_issue": v_issue,
        "insight": insight_dict,
        "created_at": report.created_at,
        "expert_reviews": reviews_list
    }


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    image: UploadFile = File(...),
    crop: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a crop leaf photo for end-to-end processing:
    1. Validation (quality, blur, lighting, leaf presence)
    2. MobileNetV2 disease classification
    3. OpenCV heuristic severity estimation
    4. Attaching comprehensive IPM cure & insight plan
    5. Persisting report and telemetry duration
    """
    start_time = time.time()
    check_rate_limit(current_user.id)

    # Read image contents
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    # Save initial file with unique UUID
    ext = Path(image.filename or "upload.jpg").suffix.lower()
    if not ext or ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    saved_image_path = Path(settings.UPLOAD_DIR) / unique_filename
    
    with open(saved_image_path, "wb") as f:
        f.write(image_bytes)

    rel_image_path = f"uploads/{unique_filename}"
    kb = get_kb()

    # Step 1: Pre-flight validation
    try:
        pil_img, bgr_img, meta = validate_leaf_image(image_bytes, filename=image.filename)
    except ImageValidationError as ve:
        duration_ms = (time.time() - start_time) * 1000
        issue_data = {
            "code": ve.code,
            "message": ve.message,
            "tips": ve.tips
        }
        report = Report(
            user_id=current_user.id,
            image_path=rel_image_path,
            crop=crop,
            location=location,
            notes=json.dumps(issue_data),
            status="needs_better_image"
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        # Log processing
        proc_log = ProcessingLog(
            report_id=report.id,
            success=False,
            error=f"Validation failed: {ve.code} - {ve.message}",
            duration_ms=duration_ms
        )
        db.add(proc_log)
        db.commit()

        return format_report_response(report, validation_issue=issue_data)

    # Step 2: MobileNetV2 Inference
    top3 = classifier.predict(pil_img)
    top_pred = top3[0] if top3 else None

    # Memory Telemetry
    from backend.utils.memory import log_memory
    log_memory("After Disease Prediction")

    if not top_pred:
        raise HTTPException(status_code=500, detail="Inference failed to produce predictions.")


    confidence = top_pred["probability"]
    predicted_class = top_pred["class_id"]
    detected_crop = top_pred["crop"]
    is_healthy = "healthy" in predicted_class.lower()

    # Confidence rules
    if confidence < settings.CONFIDENCE_REJECT_THRESHOLD:
        status_label = "low_confidence"
    elif confidence < settings.CONFIDENCE_CERTAINTY_THRESHOLD:
        status_label = "completed_low_certainty"
    else:
        status_label = "completed"

    # Step 3: Heuristic Severity Analysis (skipped if healthy or low confidence rejection)
    if is_healthy or status_label == "low_confidence":
        severity_label = None
        severity_ratio = 0.0
        overlay_path = None
    else:
        severity_label, severity_ratio, overlay_path = analyze_leaf_severity(
            bgr_img=bgr_img,
            is_healthy=False,
            output_filename=unique_filename
        )

    # Step 4: Attach Knowledge Base Insight
    insight_obj = kb.get(predicted_class)
    if status_label == "low_confidence":
        # Do not provide treatment insight on rejected low-confidence uploads
        insight_json_str = None
    else:
        insight_json_str = json.dumps(insight_obj) if insight_obj else None

    # Step 5: Save report & processing log
    duration_ms = (time.time() - start_time) * 1000
    report = Report(
        user_id=current_user.id,
        image_path=rel_image_path,
        overlay_path=overlay_path,
        crop=crop or detected_crop,
        location=location,
        notes=notes,
        predicted_class=predicted_class,
        confidence=confidence,
        top3_json=json.dumps(top3),
        severity=severity_label,
        severity_ratio=severity_ratio,
        status=status_label,
        insight_json=insight_json_str
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    proc_log = ProcessingLog(
        report_id=report.id,
        success=True,
        duration_ms=duration_ms
    )
    db.add(proc_log)
    db.commit()

    return format_report_response(report)


@router.get("", response_model=List[ReportResponse])
def get_reports(
    crop: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves filtered reports for the current user (or all if expert)."""
    query = db.query(Report)

    # Non-expert users only see their own reports
    if current_user.role != "expert":
        query = query.filter(Report.user_id == current_user.id)

    if crop:
        query = query.filter(Report.crop.ilike(f"%{crop}%"))
    if severity:
        query = query.filter(Report.severity == severity)
    if status_filter:
        query = query.filter(Report.status == status_filter)
    if search:
        s = f"%{search}%"
        query = query.filter(
            or_(
                Report.predicted_class.ilike(s),
                Report.crop.ilike(s),
                Report.notes.ilike(s),
                Report.location.ilike(s)
            )
        )

    reports = query.order_by(desc(Report.created_at)).all()
    return [format_report_response(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report_detail(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves a single report by ID."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if current_user.role != "expert" and report.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this report.")

    return format_report_response(report)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a report and associated local files."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if report.user_id != current_user.id and current_user.role != "expert":
        raise HTTPException(status_code=403, detail="Not authorized to delete this report.")

    # Remove files if they exist
    for rel_path in [report.image_path, report.overlay_path]:
        if rel_path:
            full_path = Path(rel_path)
            if full_path.exists():
                try:
                    os.remove(full_path)
                except Exception as e:
                    logger.warning(f"Failed to delete file {full_path}: {e}")

    db.delete(report)
    db.commit()
    return None
