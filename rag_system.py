import os
import re
from typing import List, Tuple
from openai import OpenAI
from models import PatientContext, MedicalFinding, ExplanationOutput
from knowledge_base import MedicalKnowledgeBase
from extractor import ReportExtractor

class MedicalRAGSystem:
    """Main RAG system with hallucination control"""
    
    def __init__(self, api_key: str, model: str, base_url: str | None = None):
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        self.client = OpenAI(**client_kwargs)
        self.model = model
        self.kb = MedicalKnowledgeBase()
        self.extractor = ReportExtractor()
        
    def initialize_knowledge_base(self, medical_sources: List[str]):
        """Load medical knowledge base"""
        self.kb.load_medical_sources(medical_sources)
        self.kb.save()
    
    def process_report(
        self, 
        report_text: str, 
        patient_context: PatientContext
    ) -> ExplanationOutput:
        """Process medical report with RAG"""
        
        # 1. Extract structured findings
        findings = self.extractor.extract_findings(report_text)
        
        # 2. Retrieve relevant medical knowledge
        retrieved_context = self.kb.retrieve(report_text, k=3)
        
        # 3. Generate grounded explanation
        explanation, confidence, uncertainties = self._generate_explanation(
            report_text, findings, retrieved_context, patient_context
        )
        
        # 4. Determine if doctor review needed
        requires_review = self._needs_doctor_review(findings, confidence)
        
        return ExplanationOutput(
            summary=self._generate_summary(findings),
            findings=findings,
            personalized_explanation=explanation,
            uncertainty_notes=uncertainties,
            confidence_score=confidence,
            sources_used=[src for _, _, src in retrieved_context],
            requires_doctor_review=requires_review
        )
    
    def _generate_explanation(
        self,
        report: str,
        findings: List[MedicalFinding],
        context: List[Tuple[str, float, str]],
        patient: PatientContext
    ) -> Tuple[str, float, List[str]]:
        """Generate personalized explanation with uncertainty tracking"""

        offline_requested = os.getenv("LLM_OFFLINE", "").strip().lower() in {"1", "true", "yes"}
        
        literacy_map = {
            "low": "very simple terms, avoid medical jargon",
            "medium": "clear language with some medical terms explained",
            "high": "technical medical terminology is acceptable"
        }
        
        context_text = "\n".join([f"- {doc}" for doc, _, _ in context])
        findings_text = "\n".join([f"- {f.finding}: {f.value or 'observed'} ({f.severity})" 
                                   for f in findings])
        
        prompt = f"""You are a medical AI assistant. Explain this report using ONLY the provided medical knowledge.

MEDICAL KNOWLEDGE BASE:
{context_text}

REPORT FINDINGS:
{findings_text}

PATIENT CONTEXT:
- Age: {patient.age}
- Medical literacy: {literacy_map[patient.medical_literacy]}
- Existing conditions: {', '.join(patient.existing_conditions) or 'None'}

INSTRUCTIONS:
1. Explain findings using ONLY information from the knowledge base
2. Use {literacy_map[patient.medical_literacy]}
3. If uncertain, explicitly state "This is unclear from available information"
4. Personalize for age {patient.age} and conditions: {patient.existing_conditions}
5. Be concise but complete

Provide explanation:"""

        if offline_requested:
            return self._generate_offline_explanation(findings, context, patient)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a medical explanation assistant. Only use provided sources. Mark uncertainties clearly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        explanation = response.choices[0].message.content
        
        # Extract uncertainty markers
        uncertainties = self._extract_uncertainties(explanation)
        
        # Calculate confidence based on retrieval scores and uncertainties
        avg_retrieval_score = sum(score for _, score, _ in context) / len(context) if context else 0
        confidence = max(0.0, min(1.0, (1 - avg_retrieval_score) * (1 - len(uncertainties) * 0.1)))
        
        return explanation, confidence, uncertainties

    def answer_question(
        self,
        question: str,
        patient: PatientContext
    ) -> Tuple[str, float, List[str], List[str]]:
        """Answer a free-form question using only the retrieved knowledge base."""

        if not self._is_medical_question(question):
            msg = (
                "I can answer questions about medical reports, lab values, and findings. "
                "Please ask a medical question (e.g., about a lab value, range, or symptom)."
            )
            return msg, 0.0, [], ["Outside medical scope"]

        context = self.kb.retrieve(question, k=3)
        sources = [src for _, _, src in context]

        offline_requested = os.getenv("LLM_OFFLINE", "").strip().lower() in {"1", "true", "yes"}

        context_text = "\n".join([f"- {doc}" for doc, _, _ in context])
        prompt = f"""You are a medical AI assistant. Answer the question using ONLY the provided medical knowledge.

MEDICAL KNOWLEDGE BASE:
{context_text}

QUESTION:
{question}

PATIENT CONTEXT:
- Age: {patient.age}
- Medical literacy: {patient.medical_literacy}
- Existing conditions: {', '.join(patient.existing_conditions) or 'None'}

INSTRUCTIONS:
1. Answer using ONLY the knowledge base
2. If uncertain, explicitly state "This is unclear from available information"
3. Be concise and clear

Provide answer:"""

        if offline_requested:
            answer, confidence, uncertainties = self._generate_offline_answer(question, context, patient)
            return answer, confidence, sources, uncertainties

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a medical explanation assistant. Only use provided sources. Mark uncertainties clearly."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        answer = response.choices[0].message.content
        uncertainties = self._extract_uncertainties(answer)
        avg_retrieval_score = sum(score for _, score, _ in context) / len(context) if context else 0
        confidence = max(0.0, min(1.0, (1 - avg_retrieval_score) * (1 - len(uncertainties) * 0.1)))
        return answer, confidence, sources, uncertainties

    def _generate_offline_explanation(
        self,
        findings: List[MedicalFinding],
        context: List[Tuple[str, float, str]],
        patient: PatientContext
    ) -> Tuple[str, float, List[str]]:
        """Generate a deterministic, offline explanation using retrieved context only."""

        lines: List[str] = []
        uncertainties: List[str] = []

        lines.append(
            "Offline mode: using retrieved medical knowledge only; no external LLM calls were made."
        )
        lines.append(
            f"Patient context: age {patient.age}; conditions: {', '.join(patient.existing_conditions) or 'None'}."
        )

        for finding in findings:
            value_text = (
                f"Value {finding.value} (normal {finding.normal_range})"
                if finding.value and finding.normal_range
                else "Value observed"
            )
            lines.append(f"{finding.finding}: {value_text}. Severity: {finding.severity}.")

            matched_doc = self._best_context_doc(finding.finding, context)
            if matched_doc:
                lines.append(f"Related knowledge: {matched_doc}")
            else:
                note = "This is unclear from available information"
                lines.append(note)
                uncertainties.append(note)

        avg_retrieval_score = sum(score for _, score, _ in context) / len(context) if context else 1.0
        confidence = max(0.0, min(1.0, (1 - avg_retrieval_score) * (1 - len(uncertainties) * 0.15)))
        confidence *= 0.8

        return "\n".join(lines), confidence, uncertainties

    def _generate_offline_answer(
        self,
        question: str,
        context: List[Tuple[str, float, str]],
        patient: PatientContext
    ) -> Tuple[str, float, List[str]]:
        """Deterministic offline answer using retrieved context only."""

        lines: List[str] = []
        uncertainties: List[str] = []

        lines.append(
            "Offline mode: using retrieved medical knowledge only; no external LLM calls were made."
        )
        lines.append(f"Question: {question}")
        lines.append(f"Patient context: age {patient.age}; conditions: {', '.join(patient.existing_conditions) or 'None'}.")

        if context:
            lines.append("Relevant knowledge:")
            for doc, _, _ in context:
                lines.append(f"- {doc}")
        else:
            note = "This is unclear from available information"
            lines.append(note)
            uncertainties.append(note)

        avg_retrieval_score = sum(score for _, score, _ in context) / len(context) if context else 1.0
        confidence = max(0.0, min(1.0, (1 - avg_retrieval_score) * (1 - len(uncertainties) * 0.15)))
        confidence *= 0.8

        return "\n".join(lines), confidence, uncertainties

    def _best_context_doc(self, finding_text: str, context: List[Tuple[str, float, str]]) -> str | None:
        """Pick the most relevant context doc by keyword overlap."""
        if not context:
            return None

        f_terms = set(re.findall(r"[a-z0-9]+", finding_text.lower()))
        if not f_terms:
            return None

        best_doc = None
        best_overlap = 0
        for doc, _, _ in context:
            d_terms = set(re.findall(r"[a-z0-9]+", doc.lower()))
            overlap = len(f_terms & d_terms)
            if overlap > best_overlap:
                best_overlap = overlap
                best_doc = doc

        return best_doc

    def _is_medical_question(self, question: str) -> bool:
        """Lightweight heuristic to detect medical-domain questions."""
        q = question.lower()
        if re.search(r"\b(mg/dl|mmhg|miu/l|ng/ml|g/dl|cells/mcl)\b", q):
            return True

        tokens = set(re.findall(r"[a-z0-9]+", q))
        medical_keywords = {
            "hemoglobin", "glucose", "cholesterol", "creatinine", "wbc", "white", "blood",
            "pressure", "tsh", "alt", "hba1c", "vitamin", "lab", "range", "anemia",
            "diabetes", "infection", "kidney", "liver", "thyroid", "test", "result",
            "report", "panel", "count", "symptom", "diagnosis", "pain", "ache", "stomach",
            "nausea", "vomit", "fever", "cough", "headache", "dizzy", "fatigue", "sick",
            "hurt", "sore", "swelling", "rash", "breathing", "chest", "heart", "medical",
            "health", "doctor", "treatment", "medication", "disease", "condition"
        }
        return bool(tokens & medical_keywords)
    
    def _extract_uncertainties(self, text: str) -> List[str]:
        """Extract uncertainty statements"""
        uncertainty_markers = ["unclear", "uncertain", "may", "might", "possibly", "not enough information"]
        uncertainties = []
        
        for sentence in text.split('.'):
            if any(marker in sentence.lower() for marker in uncertainty_markers):
                uncertainties.append(sentence.strip())
        
        return uncertainties
    
    def _generate_summary(self, findings: List[MedicalFinding]) -> str:
        """Generate brief summary"""
        critical = [f for f in findings if f.severity == "critical"]
        attention = [f for f in findings if f.severity == "attention"]
        
        if critical:
            return f"CRITICAL: {len(critical)} findings require immediate attention"
        elif attention:
            return f"{len(attention)} findings need attention, rest normal"
        return "All findings within normal ranges"
    
    def _needs_doctor_review(self, findings: List[MedicalFinding], confidence: float) -> bool:
        """Determine if doctor review is required"""
        has_critical = any(f.severity == "critical" for f in findings)
        low_confidence = confidence < 0.7
        return has_critical or low_confidence
