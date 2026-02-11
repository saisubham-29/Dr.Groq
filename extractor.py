import re
from typing import List, Dict
from models import MedicalFinding

class ReportExtractor:
    """Extract structured information from medical reports"""
    
    SEVERITY_KEYWORDS = {
        "critical": ["critical", "severe", "urgent", "emergency", "abnormal"],
        "attention": ["elevated", "high", "low", "borderline", "concern"],
        "normal": ["normal", "within range", "stable"]
    }
    
    def extract_findings(self, report_text: str) -> List[MedicalFinding]:
        """Extract key findings from report"""
        findings = []
        
        # Pattern: Test Name: Value (Range)
        pattern = r'([A-Za-z\s]+):\s*([0-9.]+)\s*(?:\(([0-9.\-\s]+)\))?'
        matches = re.findall(pattern, report_text)
        
        for match in matches:
            test_name, value, normal_range = match
            severity = self._determine_severity(report_text, test_name)
            
            findings.append(MedicalFinding(
                category="lab_test",
                finding=test_name.strip(),
                value=value,
                normal_range=normal_range if normal_range else None,
                severity=severity,
                confidence=0.85
            ))
        
        # Extract text-based findings
        sentences = report_text.split('.')
        for sent in sentences:
            if any(kw in sent.lower() for kw in ["shows", "indicates", "reveals"]):
                severity = self._determine_severity(sent, "")
                findings.append(MedicalFinding(
                    category="observation",
                    finding=sent.strip(),
                    severity=severity,
                    confidence=0.75
                ))
        
        return findings
    
    def _determine_severity(self, text: str, context: str) -> str:
        """Determine severity from text"""
        text_lower = (text + " " + context).lower()
        
        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                return severity
        return "normal"
