import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from medical_chatbot import MedicalChatbot
from appointment_booking import AppointmentBooking
import uuid

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for Android app

# Store chatbot instances per session
chatbot_sessions = {}
booking = AppointmentBooking()

def get_or_create_chatbot(session_id):
    """Get existing chatbot or create new one for session"""
    if session_id not in chatbot_sessions:
        chatbot_sessions[session_id] = MedicalChatbot()
    return chatbot_sessions[session_id]

@app.route('/')
def index():
    return render_template('chatbot.html')

# ============= REST APIs for Android =============

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """
    POST /api/chat
    Request: {
        "session_id": "optional-uuid",
        "message": "I have a headache"
    }
    Response: {
        "session_id": "uuid",
        "response": "...",
        "is_emergency": false,
        "severity": "low",
        "patient_context": {...},
        "show_booking": false
    }
    """
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get or create session
        session_id = data.get('session_id', str(uuid.uuid4()))
        message = data.get('message', '')
        
        chatbot = get_or_create_chatbot(session_id)
        
        # Check if user wants to book appointment
        if booking.detect_booking_intent(message):
            conditions = chatbot.get_patient_context().get('conditions', [])
            symptoms = chatbot.get_symptoms()
            specialty = booking.suggest_specialty(symptoms, conditions)
            slots = booking.get_available_slots(specialty)
            booking_info = booking.format_booking_response(specialty, slots)
            
            return jsonify({
                'session_id': session_id,
                'response': booking_info,
                'is_emergency': False,
                'severity': 'medium',
                'show_booking': True,
                'booking_specialty': specialty,
                'booking_slots': slots[:5],
                'patient_context': chatbot.get_patient_context()
            })
        
        result = chatbot.chat(message)
        result['session_id'] = session_id
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<session_id>', methods=['GET'])
def api_get_chat(session_id):
    """
    GET /api/chat/{session_id}
    Response: {
        "session_id": "uuid",
        "conversation_history": [...],
        "patient_context": {...},
        "symptoms": [...]
    }
    """
    try:
        if session_id not in chatbot_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        chatbot = chatbot_sessions[session_id]
        
        return jsonify({
            'session_id': session_id,
            'conversation_history': chatbot.conversation_history,
            'patient_context': chatbot.get_patient_context(),
            'symptoms': chatbot.get_symptoms()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<session_id>', methods=['DELETE'])
def api_delete_chat(session_id):
    """
    DELETE /api/chat/{session_id}
    Response: {"status": "ok"}
    """
    try:
        if session_id in chatbot_sessions:
            del chatbot_sessions[session_id]
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/booking/slots', methods=['GET'])
def api_get_slots():
    """
    GET /api/booking/slots?specialty=Cardiologist&days=7
    Response: {
        "specialty": "Cardiologist",
        "slots": [...]
    }
    """
    try:
        specialty = request.args.get('specialty', 'General Physician')
        days = int(request.args.get('days', 7))
        
        slots = booking.get_available_slots(specialty, days)
        
        return jsonify({
            'specialty': specialty,
            'slots': slots,
            'available_specialties': booking.available_specialties
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============= Web UI Routes =============

@app.route('/chat', methods=['POST'])
def chat():
    """Web UI chat endpoint"""
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Use default session for web UI
        session_id = 'web-session'
        chatbot = get_or_create_chatbot(session_id)
        
        # Check if user wants to book appointment
        if booking.detect_booking_intent(message):
            conditions = chatbot.get_patient_context().get('conditions', [])
            symptoms = chatbot.get_symptoms()
            specialty = booking.suggest_specialty(symptoms, conditions)
            slots = booking.get_available_slots(specialty)
            booking_info = booking.format_booking_response(specialty, slots)
            
            return jsonify({
                'response': booking_info,
                'is_emergency': False,
                'severity': 'medium',
                'show_booking': True,
                'booking_specialty': specialty,
                'booking_slots': slots[:5]
            })
        
        result = chatbot.chat(message)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset():
    """Web UI reset endpoint"""
    session_id = 'web-session'
    if session_id in chatbot_sessions:
        chatbot_sessions[session_id].reset()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
