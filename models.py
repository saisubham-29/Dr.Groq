from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class PatientContext(BaseModel):
    """Patient personalization context"""
    age: int
    medical_literacy: str = Field(description="low, medium, high")
    existing_conditions: List[str] = Field(default_factory=list)
    language_preference: str = "simple"

class MedicalFinding(BaseModel):
    """Structured medical finding"""
    category: str
    finding: str
    value: Optional[str] = None
    normal_range: Optional[str] = None
    severity: str = "normal"  # normal, attention, critical
    confidence: float = Field(ge=0.0, le=1.0)

class ExplanationOutput(BaseModel):
    """Final explanation with metadata"""
    summary: str
    findings: List[MedicalFinding]
    personalized_explanation: str
    uncertainty_notes: List[str]
    confidence_score: float
    sources_used: List[str]
    requires_doctor_review: bool
    doctor_notes: Optional[str] = None
