# 🩺 Medical AI Chatbot

An intelligent medical assistant powered by AI with context awareness, voice input, symptom assessment, and safety guardrails.

## ✨ Features

### 🎯 Core Capabilities
- **Multi-language Support** - Automatically detects and responds in user's language
- **Context Awareness** - Remembers patient age, conditions, and medications
- **Voice Input** - Speech-to-text for hands-free interaction
- **Symptom Assessment** - Structured questioning with follow-ups
- **Smart Recommendations** - Home care, OTC suggestions, and when to see a doctor
- **Safety Guardrails** - Emergency detection and escalation

### 🛡️ Safety Features
- **Emergency Detection** - Flags critical symptoms (chest pain, severe bleeding, etc.)
- **Severity Indicators** - Visual color-coding (red/yellow/green)
- **No Diagnosis/Prescription** - Educational information only
- **Clear Disclaimers** - Reminds users to consult healthcare professionals

### 🎨 User Experience
- Clean, modern interface
- Real-time conversation
- Patient context display
- Example questions
- Mobile-responsive design

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Groq API key (free at https://console.groq.com)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd JupyterProject
```

2. **Create virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

5. **Run the application**
```bash
python3 chatbot_app.py
```

6. **Open in browser**
```
http://localhost:5000
```

## 📋 Configuration

### Environment Variables (.env)

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile
LLM_OFFLINE=0  # Set to 1 for offline mode (no API calls)
```

### Getting a Groq API Key

1. Visit https://console.groq.com
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste into `.env` file

## 🎯 Usage

### Basic Conversation

```
User: "I'm 45 years old with diabetes. I have a headache for 2 days."

Bot: [Extracts context: age=45, condition=diabetes]
     [Asks follow-up questions about severity, location, triggers]
     [Provides personalized advice based on context]
     [Suggests home care and when to see doctor]
```

### Voice Input

1. Click the 🎤 microphone button
2. Allow microphone permissions (first time only)
3. Speak your question clearly
4. Text appears automatically in input field
5. Click Send or press Enter

**Note:** Voice input requires Chrome or Edge browser.

### Example Questions

- "What causes high blood pressure?"
- "I have a fever and sore throat. What should I do?"
- "What are the side effects of aspirin?"
- "Is 140/90 blood pressure high?"
- "I'm taking metformin. Can I take ibuprofen?"

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         User Interface (HTML/JS)        │
│  - Voice input, Chat display, Context   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│       Flask App (chatbot_app.py)        │
│  - Routes: /chat, /reset                │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│   Medical Chatbot (medical_chatbot.py)  │
│  - Context extraction                   │
│  - Emergency detection                  │
│  - Severity assessment                  │
│  - Conversation management              │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│         Groq API (LLM)                  │
│  - llama-3.3-70b-versatile              │
└─────────────────────────────────────────┘
```

## 📁 Project Structure

```
JupyterProject/
├── chatbot_app.py           # Flask application
├── medical_chatbot.py       # Core chatbot logic
├── templates/
│   └── chatbot.html         # Web interface
├── .env                     # Configuration (not in git)
├── .env.example             # Example configuration
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── DOCUMENTATION.md        # Detailed documentation
```

## 🔒 Safety & Limitations

### What the Bot CAN Do
✅ Provide educational medical information
✅ Explain symptoms, conditions, and treatments
✅ Suggest home care and OTC remedies
✅ Recommend when to see a doctor
✅ Answer questions about lab values and medications

### What the Bot CANNOT Do
❌ Diagnose medical conditions
❌ Prescribe medications
❌ Replace professional medical advice
❌ Handle true medical emergencies
❌ Provide personalized treatment plans

### Emergency Situations
For medical emergencies, the bot will display:
```
🚨 EMERGENCY ALERT
Call emergency services immediately (911/112)
```

Always seek immediate medical attention for:
- Chest pain or pressure
- Difficulty breathing
- Severe bleeding
- Loss of consciousness
- Signs of stroke
- Severe abdominal pain

## 🛠️ Development

### Running in Development Mode

```bash
# With auto-reload
python3 chatbot_app.py

# The app runs on http://localhost:5000
# Debug mode is enabled by default
```

### Adding New Features

1. **Modify system prompt** - Edit `medical_chatbot.py` → `system_prompt`
2. **Add new routes** - Edit `chatbot_app.py`
3. **Update UI** - Edit `templates/chatbot.html`

### Testing

```bash
# Test API key
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is diabetes?"}'

# Expected response
{"response": "...", "is_emergency": false, "severity": "low"}
```

## 📊 Context Extraction

The bot automatically extracts and remembers:

| Type | Examples | Detection |
|------|----------|-----------|
| Age | "I'm 45 years old" | Regex pattern |
| Conditions | diabetes, hypertension, asthma | Keyword matching |
| Medications | aspirin, metformin, insulin | Keyword matching |

Context is displayed at the top of the chat and used to personalize all responses.

## 🌍 Multi-language Support

The bot automatically detects the language of the user's question and responds in the same language.

**Supported languages:** All languages supported by the LLM (100+)

Example:
```
User: "¿Qué causa la presión arterial alta?"
Bot: [Responds in Spanish]
```

## 🐛 Troubleshooting

### Voice Input Not Working
- **Use Chrome or Edge** (Firefox/Safari not supported)
- **Check microphone permissions** in browser settings
- **Use HTTPS or localhost** (required by Web Speech API)
- **Check console** (F12) for error messages

### API Errors
- **401 Invalid API Key** - Check `.env` file, get new key from Groq
- **429 Rate Limit** - Wait a few minutes, Groq has rate limits
- **500 Server Error** - Check Flask logs for details

### Bot Not Responding
- **Check Flask is running** - Should see "Running on http://127.0.0.1:5000"
- **Check browser console** - Look for JavaScript errors
- **Verify API key** - Test with curl command above

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues or questions:
- Open a GitHub issue
- Check existing documentation
- Review troubleshooting section

## 🙏 Acknowledgments

- **Groq** - Fast LLM inference
- **Llama 3.3** - Base language model
- **Web Speech API** - Voice input functionality

---

**⚠️ Medical Disclaimer:** This is an educational AI assistant, not a medical professional. Always consult qualified healthcare providers for medical advice, diagnosis, or treatment. In emergencies, call emergency services immediately.
