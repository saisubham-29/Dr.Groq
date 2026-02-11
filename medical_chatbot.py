import os
import re
from openai import OpenAI
from dotenv import load_dotenv
from typing import List

load_dotenv()

class MedicalChatbot:
    """General medical chatbot with guardrails"""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        base_url = "https://api.groq.com/openai/v1"
        
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.conversation_history = []
        self.patient_context = {}
        self.symptoms = []  # Track symptoms for booking
        
        self.system_prompt = """You are an empathetic medical AI assistant. Follow these rules:

1. PATIENT CONTEXT:
   - Remember patient details: age, existing conditions, medications, allergies
   - Personalize responses based on context
   - Ask for relevant details if missing

2. SYMPTOM ASSESSMENT:
   - Ask follow-up questions to understand symptoms better (duration, severity, triggers, associated symptoms)
   - Use structured approach: WHEN did it start? WHERE is it? HOW severe (1-10)? WHAT makes it better/worse?
   - Gather enough information before suggesting next steps

3. RESPONSE STRUCTURE:
   - Start with empathy: "I understand this must be concerning..."
   - Ask clarifying questions if needed
   - Provide clear, detailed explanation
   - Suggest home care options (rest, hydration, OTC remedies)
   - Recommend when to see a doctor
   - Flag serious symptoms immediately

4. APPOINTMENT BOOKING:
   - Only help with booking when user explicitly requests it
   - User must ask to "book appointment" or "schedule appointment"
   - Do NOT automatically suggest booking
   - When asked, provide helpful information about seeing a doctor

5. SAFETY & GUARDRAILS:
   - RED FLAGS (seek immediate care): chest pain, difficulty breathing, severe bleeding, sudden severe headache, confusion, loss of consciousness, severe abdominal pain, signs of stroke
   - YELLOW FLAGS (see doctor soon): persistent fever, worsening symptoms, symptoms lasting >1 week
   - Never diagnose or prescribe prescription medication
   - Can suggest OTC remedies (e.g., "You might consider acetaminophen for fever, but check with pharmacist")

6. HOME CARE SUGGESTIONS:
   - Rest, hydration, nutrition
   - OTC medications (with cautions)
   - When to monitor symptoms
   - Warning signs to watch for

7. MULTILINGUAL:
   - Detect and respond in user's language
   - Maintain medical accuracy

Be warm, thorough, and safety-focused."""

    def chat(self, user_message: str) -> dict:
        """Process user message and return response"""
        
        # Extract patient context and symptoms
        self._extract_patient_context(user_message)
        self._extract_symptoms(user_message)
        
        # Check for emergency keywords
        emergency_keywords = ["chest pain", "can't breathe", "can not breathe", "cannot breathe",
                            "severe bleeding", "unconscious", "suicide", "overdose", 
                            "heart attack", "stroke", "severe headache", "confused",
                            "loss of consciousness", "severe abdominal pain"]
        if any(keyword in user_message.lower() for keyword in emergency_keywords):
            return {
                "response": "🚨 **EMERGENCY ALERT**\n\nThis sounds like a medical emergency. Please:\n\n1. **Call emergency services immediately** (911 in US, 112 in EU, or your local emergency number)\n2. **Go to the nearest emergency room**, or\n3. **Call your doctor immediately**\n\nDo not wait. Seek help now.",
                "is_emergency": True,
                "severity": "critical",
                "show_booking": False
            }
        
        # Build context-aware message
        context_info = self._build_context_string()
        enhanced_message = f"{context_info}\n\nUser message: {user_message}" if context_info else user_message
        
        # Add to history
        self.conversation_history.append({"role": "user", "content": enhanced_message})
        
        # Keep last 12 messages
        if len(self.conversation_history) > 12:
            self.conversation_history = self.conversation_history[-12:]
        
        # Generate response
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    *self.conversation_history
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            assistant_message = response.choices[0].message.content
            
            # Determine severity
            severity = self._assess_severity(assistant_message)
            
            # Check if booking should be offered
            show_booking = self._should_offer_booking(assistant_message, severity)
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return {
                "response": assistant_message,
                "is_emergency": False,
                "severity": severity,
                "patient_context": self.patient_context,
                "show_booking": show_booking,
                "symptoms": self.symptoms
            }
            
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "is_emergency": False,
                "severity": "none",
                "show_booking": False
            }
    
    def _extract_patient_context(self, message: str):
        """Extract patient details from conversation"""
        msg_lower = message.lower()
        
        # Extract age
        import re
        age_match = re.search(r'\b(\d{1,3})\s*(?:years?|yrs?|yo)\b', msg_lower)
        if age_match:
            self.patient_context['age'] = age_match.group(1)
        
        # Extract conditions
        conditions = ['diabetes', 'hypertension', 'asthma', 'heart disease', 'kidney disease', 
                     'liver disease', 'cancer', 'copd', 'arthritis', 'depression', 'anxiety']
        for condition in conditions:
            if condition in msg_lower:
                if 'conditions' not in self.patient_context:
                    self.patient_context['conditions'] = []
                if condition not in self.patient_context['conditions']:
                    self.patient_context['conditions'].append(condition)
        
        # Extract medications
        if 'taking' in msg_lower or 'medication' in msg_lower or 'medicine' in msg_lower:
            med_keywords = ['aspirin', 'metformin', 'insulin', 'lisinopril', 'atorvastatin', 
                          'amlodipine', 'omeprazole', 'levothyroxine', 'albuterol']
            for med in med_keywords:
                if med in msg_lower:
                    if 'medications' not in self.patient_context:
                        self.patient_context['medications'] = []
                    if med not in self.patient_context['medications']:
                        self.patient_context['medications'].append(med)
    
    def _build_context_string(self) -> str:
        """Build context string for LLM"""
        if not self.patient_context:
            return ""
        
        parts = ["Patient context:"]
        if 'age' in self.patient_context:
            parts.append(f"Age: {self.patient_context['age']}")
        if 'conditions' in self.patient_context:
            parts.append(f"Conditions: {', '.join(self.patient_context['conditions'])}")
        if 'medications' in self.patient_context:
            parts.append(f"Medications: {', '.join(self.patient_context['medications'])}")
        
        return " | ".join(parts)
    
    def _extract_symptoms(self, message: str):
        """Extract symptoms from message"""
        symptom_keywords = [
            'pain', 'ache', 'fever', 'cough', 'nausea', 'vomit', 'dizzy',
            'headache', 'fatigue', 'weakness', 'bleeding', 'rash', 'swelling',
            'breathing', 'chest', 'stomach', 'throat', 'sore', 'hurt'
        ]
        
        msg_lower = message.lower()
        for symptom in symptom_keywords:
            if symptom in msg_lower and symptom not in self.symptoms:
                self.symptoms.append(symptom)
    
    def _should_offer_booking(self, response: str, severity: str) -> bool:
        """Determine if appointment booking should be offered"""
        # Only offer booking if explicitly requested by user
        # Don't auto-suggest based on severity
        return False
    
    def _assess_severity(self, response: str) -> str:
        """Assess severity from response"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['emergency', 'immediately', 'urgent', 'call 911', 'er']):
            return 'high'
        elif any(word in response_lower for word in ['see a doctor', 'medical attention', 'consult']):
            return 'medium'
        else:
            return 'low'
    
    def reset(self):
        """Clear conversation history"""
        self.conversation_history = []
        self.patient_context = {}
        self.symptoms = []
    
    def get_patient_context(self) -> dict:
        """Get current patient context"""
        return self.patient_context
    
    def get_symptoms(self) -> List[str]:
        """Get tracked symptoms"""
        return self.symptoms
