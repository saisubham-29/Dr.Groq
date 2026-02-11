import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from medical_chatbot import MedicalChatbot

load_dotenv()

app = Flask(__name__)
chatbot = MedicalChatbot()

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
