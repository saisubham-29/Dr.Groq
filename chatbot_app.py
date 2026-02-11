import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from medical_chatbot import MedicalChatbot
from appointment_booking import AppointmentBooking

load_dotenv()

app = Flask(__name__)
chatbot = MedicalChatbot()
booking = AppointmentBooking()

@app.route('/')
def index():
    return render_template('chatbot.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
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
    chatbot.reset()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
