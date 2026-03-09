# AI-Powered Medical Report Intelligence System

A trustworthy medical RAG system with hallucination control, personalization, and doctor verification.

## Features

✅ **Retrieval-Augmented Generation (RAG)** - Grounds explanations in verified medical sources using FAISS  
✅ **Structured Information Extraction** - Extracts key findings, values, and trends  
✅ **Personalization Layer** - Age, condition, and literacy-aware explanations  
✅ **Confidence & Uncertainty Indicators** - Explicit "known vs unclear" markers  
✅ **Human-in-the-Loop** - Doctor verification interface  
✅ **Hallucination Control** - Only uses grounded medical knowledge  

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file:
```bash
cp .env.example .env
# Add your GROQ_API_KEY (recommended) or OPENAI_API_KEY
# Optional: set LLM_PROVIDER=groq and LLM_MODEL
```

3. Run the web UI:
```bash
python3 app.py
```
Then open http://localhost:5000 in your browser.

Or run the CLI demo:
```bash
python3 main.py
```

Interactive Q&A:
```bash
python3 main.py --chat
```

Chat-only mode:
```bash
python3 main.py --chat-only
```

## Architecture

```
Medical Report → Extractor → Structured Findings
                     ↓
              RAG Retrieval (FAISS)
                     ↓
              LLM + Grounding → Personalized Explanation
                     ↓
              Confidence Check → Doctor Review (if needed)
```

## Components

- `models.py` - Data structures (PatientContext, MedicalFinding, ExplanationOutput)
- `knowledge_base.py` - FAISS vector store for medical knowledge
- `extractor.py` - Structured information extraction
- `rag_system.py` - Main RAG pipeline with hallucination control
- `doctor_interface.py` - Human-in-the-loop verification
- `main.py` - Demo application

## Usage

```python
from rag_system import MedicalRAGSystem
from models import PatientContext

# Initialize (Groq example)
system = MedicalRAGSystem(
    api_key="your-groq-key",
    model="llama-3.3-70b-versatile",
    base_url="https://api.groq.com/openai/v1"
)
system.initialize_knowledge_base(medical_sources)

# Process report
patient = PatientContext(age=55, medical_literacy="medium")
result = system.process_report(report_text, patient)

# Check if doctor review needed
if result.requires_doctor_review:
    doctor_interface.submit_for_review(report_id, result)
```

## Safety Features

- **Grounded Generation**: Only uses retrieved medical knowledge
- **Uncertainty Tracking**: Explicitly marks unclear information
- **Confidence Scoring**: Based on retrieval quality and uncertainties
- **Automatic Escalation**: Critical findings trigger doctor review
- **Verification Loop**: Doctor can approve/reject AI explanations

## Customization

Add your medical knowledge sources in `main.py`:
```python
MEDICAL_KNOWLEDGE = [
    "Your medical reference text here...",
    # Add more sources
]
```

Adjust patient context:
```python
patient = PatientContext(
    age=45,
    medical_literacy="low",  # low, medium, high
    existing_conditions=["Diabetes", "Hypertension"]
)
```
