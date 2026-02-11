import os
import argparse
from dotenv import load_dotenv
from models import PatientContext
from rag_system import MedicalRAGSystem
from doctor_interface import DoctorInterface

# Sample medical knowledge base
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

def run_demo(rag_system: MedicalRAGSystem, patient: PatientContext):
    doctor_interface = DoctorInterface()

    # Sample medical report
    sample_report = """
    Patient Blood Test Results:
    
    Hemoglobin: 10.2 (13.5-17.5)
    Blood Glucose Fasting: 118 (70-100)
    Total Cholesterol: 245 (below 200)
    Creatinine: 1.1 (0.7-1.3)
    White Blood Cell Count: 12500 (4000-11000)
    
    Impression: Shows elevated glucose levels. Cholesterol is high. 
    Hemoglobin is below normal range indicating possible anemia.
    WBC count slightly elevated, may indicate mild infection.
    """

    print("\n" + "="*60)
    print("PROCESSING MEDICAL REPORT")
    print("="*60)

    # Process report
    result = rag_system.process_report(sample_report, patient)

    # Display results
    print(f"\nSUMMARY: {result.summary}")
    print(f"CONFIDENCE: {result.confidence_score:.2%}")

    print(f"\nFINDINGS ({len(result.findings)}):")
    for finding in result.findings:
        print(f"  [{finding.severity.upper()}] {finding.finding}")
        if finding.value:
            print(f"    Value: {finding.value} (Normal: {finding.normal_range})")

    print(f"\nPERSONALIZED EXPLANATION:")
    print(result.personalized_explanation)

    if result.uncertainty_notes:
        print(f"\nUNCERTAINTIES:")
        for note in result.uncertainty_notes:
            print(f"  ⚠️  {note}")

    print(f"\nSOURCES USED: {len(result.sources_used)} medical references")

    # Doctor review workflow
    if result.requires_doctor_review:
        doctor_interface.submit_for_review("REPORT_001", result)

        # Simulate doctor verification
        print("\n[Simulating doctor review...]")
        verified = doctor_interface.doctor_verify(
            "REPORT_001", 
            approved=True,
            notes="AI explanation is accurate. Patient should follow up for anemia treatment and diabetes management."
        )

        if verified:
            print("\n✅ Report verified and ready for patient delivery")

def run_chat(rag_system: MedicalRAGSystem, patient: PatientContext):
    print("\n" + "="*60)
    print("INTERACTIVE Q&A (type 'exit' to quit)")
    print("="*60)
    while True:
        question = input("\nQuestion> ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            break
        answer, confidence, sources, uncertainties = rag_system.answer_question(question, patient)
        print("\nANSWER:")
        print(answer)
        print(f"\nCONFIDENCE: {confidence:.2%}")
        if uncertainties:
            print("UNCERTAINTIES:")
            for note in uncertainties:
                print(f"  ⚠️  {note}")
        if sources:
            print(f"SOURCES USED: {len(sources)} medical references")

def main():
    parser = argparse.ArgumentParser(description="Medical RAG demo")
    parser.add_argument("--chat", action="store_true", help="Start interactive Q&A after demo")
    parser.add_argument("--chat-only", action="store_true", help="Interactive Q&A only (skip demo)")
    args = parser.parse_args()

    # Load environment
    load_dotenv(override=True)
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("LLM_MODEL")

    if provider == "groq" or (groq_key and not openai_key):
        api_key = groq_key
        base_url = os.getenv("GROQ_BASE_URL") or "https://api.groq.com/openai/v1"
        default_model = "llama-3.3-70b-versatile"
        provider_name = "groq"
    elif openai_key:
        api_key = openai_key
        base_url = os.getenv("OPENAI_BASE_URL") or None
        default_model = "gpt-3.5-turbo"
        provider_name = "openai"
    else:
        print("ERROR: Set GROQ_API_KEY or OPENAI_API_KEY in .env file")
        return

    model = model or default_model
    
    # Initialize system
    print(f"Initializing Medical RAG System ({provider_name}, model={model})...")
    rag_system = MedicalRAGSystem(api_key=api_key, model=model, base_url=base_url)
    rag_system.initialize_knowledge_base(MEDICAL_KNOWLEDGE)

    # Patient context
    patient = PatientContext(
        age=55,
        medical_literacy="medium",
        existing_conditions=["Type 2 Diabetes"],
        language_preference="simple"
    )

    if not args.chat_only:
        run_demo(rag_system, patient)
    if args.chat or args.chat_only:
        run_chat(rag_system, patient)

if __name__ == "__main__":
    main()
