import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field


# ================= User / Auth Schemas =================
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: str = Field(default="farmer", pattern="^(farmer|expert)$")
    preferred_language: str = Field(default="en", pattern="^(en|hi|pa)$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    preferred_language: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ================= ML & Insight Schemas =================
class ClassPrediction(BaseModel):
    class_id: str
    crop: str
    disease_name: str
    probability: float


class ChemicalOption(BaseModel):
    active_ingredient: str
    note: str
    caution: str


class SeverityPlan(BaseModel):
    immediate_actions: List[str] = []
    organic_options: List[str] = []
    chemical_options: List[ChemicalOption] = []


class TreatmentBySeverity(BaseModel):
    Low: SeverityPlan
    Medium: SeverityPlan
    High: SeverityPlan


class FAQItem(BaseModel):
    q: str
    a: str
    keywords: List[str] = []


class DiseaseInsight(BaseModel):
    class_id: str
    crop: str
    disease_name: str
    scientific_name: str
    disease_type: str  # fungal/bacterial/viral/pest/nutrient/healthy
    summary: str
    symptoms: List[str]
    causes_and_spread: List[str]
    treatment_by_severity: TreatmentBySeverity
    fertilizer_and_nutrition: List[str]
    precautions_and_prevention: List[str]
    recovery_outlook: str
    when_to_consult_expert: str
    faq: List[FAQItem]
    verified: bool = False
    source_notes: str


# ================= Report Schemas =================
class ValidationIssue(BaseModel):
    code: str
    message: str
    tips: List[str]


class ReportResponse(BaseModel):
    id: int
    user_id: int
    image_path: str
    overlay_path: Optional[str] = None
    crop: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    predicted_class: Optional[str] = None
    confidence: Optional[float] = None
    top3: List[ClassPrediction] = []
    severity: Optional[str] = None
    severity_ratio: Optional[float] = None
    status: str
    validation_issue: Optional[ValidationIssue] = None
    insight: Optional[DiseaseInsight] = None
    created_at: datetime.datetime
    expert_reviews: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


# ================= Chat Schemas =================
class ChatMessage(BaseModel):
    id: Optional[int] = None
    role: str
    content: str
    created_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    report_id: Optional[int] = None
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    detected_intent: Optional[str] = None
    language: str = "en"
    quick_chips: List[str] = []


class ConversationResponse(BaseModel):
    id: int
    report_id: Optional[int] = None
    title: str
    created_at: datetime.datetime
    messages: List[ChatMessage] = []

    class Config:
        from_attributes = True


# ================= Expert Review Schemas =================
class ExpertReviewCreate(BaseModel):
    verdict: str = Field(..., pattern="^(agree|disagree|needs_more_info)$")
    comment: str = Field(..., min_length=3)


class ExpertReviewResponse(BaseModel):
    id: int
    report_id: int
    expert_id: int
    expert_name: str
    verdict: str
    comment: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ================= Metrics & Helpers =================
class MetricsSummary(BaseModel):
    total_processed: int
    successful_runs: int
    failed_runs: int
    success_rate_percent: float
    avg_duration_ms: float
    total_reports: int
    total_users: int


class SupportedCropsResponse(BaseModel):
    crops: List[str]
    total_classes: int
    classes: List[str]
    disclaimer: str
