# Medical AI Chatbot - Technical Documentation

## Table of Contents
1. [System Architecture](#system-architecture)
2. [Core Components](#core-components)
3. [API Reference](#api-reference)
4. [Prompt Engineering](#prompt-engineering)
5. [Context Management](#context-management)
6. [Safety Systems](#safety-systems)
7. [Deployment](#deployment)

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│  - HTML/CSS/JavaScript                                   │
│  - Web Speech API (voice input)                          │
│  - Real-time UI updates                                  │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/JSON
┌────────────────────▼────────────────────────────────────┐
│                  Application Layer                       │
│  - Flask web server                                      │
│  - Request routing                                       │
│  - Session management                                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                   Business Logic                         │
│  - MedicalChatbot class                                  │
│  - Context extraction                                    │
│  - Emergency detection                                   │
│  - Severity assessment                                   │
└────────────────────┬────────────────────────────────────┘
                     │ OpenAI API
┌────────────────────▼────────────────────────────────────┐
│                    LLM Provider                          │
│  - Groq API (llama-3.3-70b-versatile)                   │
│  - Response generation                                   │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### 1. MedicalChatbot Class (`medical_chatbot.py`)

**Purpose:** Core chatbot logic with context awareness and safety features.

**Key Methods:**

#### `__init__()`
Initializes the chatbot with API credentials and system prompt.

```python
def __init__(self):
    self.client = OpenAI(api_key, base_url)
    self.model = "llama-3.3-70b-versatile"
    self.conversation_history = []
    self.patient_context = {}
```

#### `chat(user_message: str) -> dict`
Main method for processing user messages.

**Flow:**
1. Extract patient context from message
2. Check for emergency keywords
3. Build context-aware prompt
4. Call LLM API
5. Assess severity
6. Return structured response

**Returns:**
```python
{
    "response": str,           # Bot's response
    "is_emergency": bool,      # True if emergency detected
    "severity": str,           # "low", "medium", "high"
    "patient_context": dict    # Extracted context
}
```

#### `_extract_patient_context(message: str)`
Extracts patient information using regex and keyword matching.

**Extracts:**
- Age: `\b(\d{1,3})\s*(?:years?|yrs?|yo)\b`
- Conditions: Keyword list (diabetes, hypertension, etc.)
- Medications: Keyword list (aspirin, metformin, etc.)

**Example:**
```python
Input: "I'm 45 years old with diabetes taking metformin"
Output: {
    "age": "45",
    "conditions": ["diabetes"],
    "medications": ["metformin"]
}
```

#### `_assess_severity(response: str) -> str`
Determines severity based on response content.

**Logic:**
- **High:** Contains "emergency", "immediately", "urgent", "call 911"
- **Medium:** Contains "see a doctor", "medical attention", "consult"
- **Low:** General information, home care

### 2. Flask Application (`chatbot_app.py`)

**Routes:**

#### `GET /`
Serves the main chatbot interface.

```python
@app.route('/')
def index():
    return render_template('chatbot.html')
```

#### `POST /chat`
Handles chat messages.

**Request:**
```json
{
    "message": "I have a headache"
}
```

**Response:**
```json
{
    "response": "I understand...",
    "is_emergency": false,
    "severity": "low",
    "patient_context": {"age": "45"}
}
```

#### `POST /reset`
Clears conversation history and patient context.

### 3. Frontend (`templates/chatbot.html`)

**Key Features:**

#### Voice Input
Uses Web Speech API for speech-to-text.

```javascript
recognition = new webkitSpeechRecognition();
recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    // Populate input field
};
```

**Browser Support:**
- ✅ Chrome/Edge
- ❌ Firefox/Safari

#### Context Display
Shows extracted patient information at top of chat.

```javascript
function updatePatientContext(context) {
    // Display age, conditions, medications
}
```

#### Severity Indicators
Visual color-coding based on severity.

```css
.severity-high { border-left: 4px solid #dc3545; }   /* Red */
.severity-medium { border-left: 4px solid #ffc107; } /* Yellow */
.severity-low { border-left: 4px solid #28a745; }    /* Green */
```

## API Reference

### Chat Endpoint

**URL:** `POST /chat`

**Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
    "message": "string (required)"
}
```

**Response:**
```json
{
    "response": "string",
    "is_emergency": boolean,
    "severity": "low" | "medium" | "high",
    "patient_context": {
        "age": "string",
        "conditions": ["string"],
        "medications": ["string"]
    }
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad request (missing message)
- `500` - Server error

**Example:**
```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is diabetes?"}'
```

### Reset Endpoint

**URL:** `POST /reset`

**Response:**
```json
{
    "status": "ok"
}
```

## Prompt Engineering

### System Prompt Structure

The system prompt is carefully designed with multiple sections:

#### 1. Patient Context
```
Remember patient details: age, existing conditions, medications, allergies
Personalize responses based on context
Ask for relevant details if missing
```

#### 2. Symptom Assessment
```
Ask follow-up questions: WHEN, WHERE, HOW severe, WHAT triggers
Use structured approach
Gather enough information before suggesting next steps
```

#### 3. Response Structure
```
1. Start with empathy
2. Ask clarifying questions
3. Provide clear explanation
4. Suggest home care
5. Recommend when to see doctor
6. Flag serious symptoms
```

#### 4. Safety Guardrails
```
RED FLAGS: chest pain, difficulty breathing, severe bleeding...
YELLOW FLAGS: persistent fever, worsening symptoms...
Never diagnose or prescribe
Can suggest OTC remedies with cautions
```

### Prompt Optimization

**Temperature:** `0.7`
- Balanced between creativity and consistency
- Allows natural conversation while maintaining accuracy

**Max Tokens:** `800`
- Sufficient for detailed responses
- Prevents overly long responses

**Context Window:** Last 12 messages
- Maintains conversation flow
- Prevents context overflow

## Context Management

### Context Lifecycle

```
User Message → Extract Context → Update State → Build Prompt → LLM Call
                     ↓
              Patient Context
              {age, conditions, meds}
                     ↓
              Persists across conversation
                     ↓
              Reset on /reset endpoint
```

### Context Injection

Context is injected into each LLM call:

```python
context_info = "Patient context: Age: 45 | Conditions: diabetes"
enhanced_message = f"{context_info}\n\nUser message: {user_message}"
```

This ensures the LLM always has patient context for personalized responses.

## Safety Systems

### Emergency Detection

**Trigger Keywords:**
```python
emergency_keywords = [
    "chest pain", "can't breathe", "severe bleeding",
    "unconscious", "suicide", "overdose",
    "heart attack", "stroke", "severe headache",
    "confused", "loss of consciousness"
]
```

**Response:**
```
🚨 EMERGENCY ALERT
Call emergency services immediately (911/112)
Go to nearest emergency room
Do not wait
```

### Severity Assessment

**Algorithm:**
1. Analyze response text for keywords
2. Classify as high/medium/low
3. Apply visual indicators
4. Guide user action

**Severity Levels:**

| Level | Indicators | Action |
|-------|-----------|--------|
| High | "emergency", "immediately" | Seek immediate care |
| Medium | "see a doctor", "consult" | Schedule appointment |
| Low | General info, home care | Self-care possible |

### Guardrails

**Built into system prompt:**
- Never diagnose conditions
- Never prescribe prescription medications
- Always include disclaimers
- Escalate when uncertain
- Suggest professional consultation

## Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY=your_key_here

# Run development server
python3 chatbot_app.py
```

### Production Deployment

#### Option 1: Gunicorn (Linux/Mac)

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn -w 4 -b 0.0.0.0:5000 chatbot_app:app
```

#### Option 2: Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV GROQ_API_KEY=""
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "chatbot_app:app"]
```

```bash
docker build -t medical-chatbot .
docker run -p 5000:5000 -e GROQ_API_KEY=your_key medical-chatbot
```

#### Option 3: Cloud Platforms

**Heroku:**
```bash
# Create Procfile
echo "web: gunicorn chatbot_app:app" > Procfile

# Deploy
heroku create
heroku config:set GROQ_API_KEY=your_key
git push heroku main
```

**AWS Elastic Beanstalk:**
```bash
eb init -p python-3.11 medical-chatbot
eb create medical-chatbot-env
eb setenv GROQ_API_KEY=your_key
eb deploy
```

### Environment Variables

**Required:**
```bash
GROQ_API_KEY=gsk_...
```

**Optional:**
```bash
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_OFFLINE=0
FLASK_ENV=production
```

### Security Considerations

1. **API Key Protection**
   - Never commit `.env` to git
   - Use environment variables in production
   - Rotate keys regularly

2. **Rate Limiting**
   - Implement rate limiting for production
   - Use Flask-Limiter or similar

3. **Input Validation**
   - Sanitize user input
   - Limit message length
   - Prevent injection attacks

4. **HTTPS**
   - Required for voice input
   - Use SSL certificates in production

### Monitoring

**Key Metrics:**
- Response time
- Error rate
- API usage
- User sessions
- Emergency detections

**Logging:**
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log important events
logger.info(f"Emergency detected: {message}")
logger.error(f"API error: {error}")
```

## Performance Optimization

### Caching
- Cache common medical information
- Use Redis for session storage

### Async Processing
- Use async/await for API calls
- Implement background tasks for logging

### Load Balancing
- Use multiple workers
- Implement horizontal scaling

## Testing

### Unit Tests
```python
def test_context_extraction():
    chatbot = MedicalChatbot()
    chatbot._extract_patient_context("I'm 45 with diabetes")
    assert chatbot.patient_context['age'] == '45'
    assert 'diabetes' in chatbot.patient_context['conditions']
```

### Integration Tests
```python
def test_chat_endpoint():
    response = client.post('/chat', json={'message': 'test'})
    assert response.status_code == 200
    assert 'response' in response.json
```

### End-to-End Tests
- Test full conversation flows
- Verify emergency detection
- Check context persistence

---

**Last Updated:** 2026-02-11
**Version:** 1.0.0
