from typing import Optional
from models import ExplanationOutput

class DoctorInterface:
    """Human-in-the-loop verification interface"""
    
    def __init__(self):
        self.pending_reviews = []
    
    def submit_for_review(self, report_id: str, output: ExplanationOutput):
        """Submit AI output for doctor review"""
        self.pending_reviews.append({
            "report_id": report_id,
            "output": output,
            "status": "pending"
        })
        print(f"\n{'='*60}")
        print(f"DOCTOR REVIEW REQUIRED - Report ID: {report_id}")
        print(f"{'='*60}")
        print(f"Reason: {'Critical findings' if any(f.severity == 'critical' for f in output.findings) else 'Low confidence'}")
        print(f"Confidence Score: {output.confidence_score:.2f}")
        print(f"\nAI Summary: {output.summary}")
        print(f"\nFindings:")
        for f in output.findings:
            print(f"  - [{f.severity.upper()}] {f.finding}: {f.value or 'N/A'}")
        print(f"\nAI Explanation:\n{output.personalized_explanation}")
        print(f"\nUncertainties:")
        for u in output.uncertainty_notes:
            print(f"  - {u}")
        print(f"{'='*60}\n")
    
    def doctor_verify(self, report_id: str, approved: bool, notes: Optional[str] = None):
        """Doctor verification"""
        for review in self.pending_reviews:
            if review["report_id"] == report_id:
                review["status"] = "approved" if approved else "rejected"
                review["output"].doctor_notes = notes
                print(f"Report {report_id} {'APPROVED' if approved else 'REJECTED'} by doctor")
                if notes:
                    print(f"Doctor notes: {notes}")
                return review["output"]
        return None
    
    def get_pending_reviews(self):
        """Get all pending reviews"""
        return [r for r in self.pending_reviews if r["status"] == "pending"]
