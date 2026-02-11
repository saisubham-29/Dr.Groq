import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from models import PatientContext
from rag_system import MedicalRAGSystem
from doctor_interface import DoctorInterface

load_dotenv()

app = Flask(__name__)

# Initialize system
api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
base_url = "https://api.groq.com/openai/v1" if os.getenv("GROQ_API_KEY") else None
rag_system = MedicalRAGSystem(api_key, model, base_url) if api_key else None
doctor_interface = DoctorInterface()

# Medical knowledge base
MEDICAL_KNOWLEDGE = [
    "Hemoglobin (Hb) normal range: 13.5-17.5 g/dL for men, 12.0-15.5 g/dL for women. Low hemoglobin indicates anemia, which can cause fatigue and weakness.",
    "Blood glucose fasting normal range: 70-100 mg/dL. Values 100-125 mg/dL indicate prediabetes. Above 126 mg/dL indicates diabetes.",
    "Total cholesterol normal: below 200 mg/dL. 200-239 mg/dL is borderline high. Above 240 mg/dL is high and increases heart disease risk.",
    "Blood pressure normal: systolic below 120 mmHg and diastolic below 80 mmHg. Hypertension is diagnosed at 130/80 mmHg or higher.",
    "Creatinine normal range: 0.7-1.3 mg/dL for men, 0.6-1.1 mg/dL for women. Elevated creatinine may indicate kidney dysfunction.",
    "White blood cell count normal: 4,000-11,000 cells/mcL. Elevated WBC may indicate infection or inflammation.",
    "Thyroid TSH normal range: 0.4-4.0 mIU/L. High TSH indicates hypothyroidism, low TSH indicates hyperthyroidism.",
    "Liver enzyme ALT normal: 7-56 units/L. Elevated ALT indicates liver damage or inflammation.",
    "HbA1c normal: below 5.7%. 5.7-6.4% indicates prediabetes. 6.5% or higher indicates diabetes.",
    "Vitamin D sufficient: above 30 ng/mL. 20-30 ng/mL is insufficient. Below 20 ng/mL is deficient."
]

if rag_system:
    rag_system.initialize_knowledge_base(MEDICAL_KNOWLEDGE)

@app.route('/')
def index():
    return render_template('chat.html')

@app.route('/report')
def report():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if not rag_system:
            return jsonify({'error': 'API key not configured'}), 500
        
        data = request.json
        report_text = data.get('report', '')
        age = data.get('age', 50)
        literacy = data.get('literacy', 'medium')
        conditions = data.get('conditions', [])
        
        patient = PatientContext(
            age=age,
            medical_literacy=literacy,
            existing_conditions=conditions
        )
        
        result = rag_system.process_report(report_text, patient)
        
        return jsonify({
            'summary': result.summary,
            'explanation': result.personalized_explanation,
            'findings': [
                {
                    'finding': f.finding,
                    'value': f.value,
                    'severity': f.severity,
                    'confidence': f.confidence
                } for f in result.findings
            ],
            'confidence': result.confidence_score,
            'uncertainties': result.uncertainty_notes,
            'requires_review': result.requires_doctor_review
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    try:
        if not rag_system:
            return jsonify({'error': 'API key not configured'}), 500
        
        data = request.json
        question = data.get('question', '')
        age = data.get('age', 50)
        literacy = data.get('literacy', 'medium')
        conditions = data.get('conditions', [])
        
        patient = PatientContext(
            age=age,
            medical_literacy=literacy,
            existing_conditions=conditions
        )
        
        answer, confidence, sources, uncertainties = rag_system.answer_question(question, patient)
        
        return jsonify({
            'answer': answer,
            'confidence': confidence,
            'sources': sources,
            'uncertainties': uncertainties
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
