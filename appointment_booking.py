import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List

class AppointmentBooking:
    """Handles appointment booking through Chronic Care"""
    
    def __init__(self):
        self.appointments = []  # In production, use database
        self.available_specialties = [
            "General Physician",
            "Cardiologist",
            "Endocrinologist",
            "Neurologist",
            "Dermatologist",
            "Orthopedic",
            "Gastroenterologist",
            "Pulmonologist"
        ]
    
    def detect_booking_intent(self, message: str) -> bool:
        """Check if user wants to book appointment"""
        booking_keywords = [
            "book appointment", "schedule appointment", "see a doctor",
            "need appointment", "want to consult", "visit doctor",
            "book doctor", "appointment", "consultation"
        ]
        return any(keyword in message.lower() for keyword in booking_keywords)
    
    def suggest_specialty(self, symptoms: List[str], conditions: List[str]) -> str:
        """Suggest appropriate specialty based on symptoms/conditions"""
        
        # Map conditions to specialties
        condition_map = {
            "diabetes": "Endocrinologist",
            "hypertension": "Cardiologist",
            "heart": "Cardiologist",
            "asthma": "Pulmonologist",
            "breathing": "Pulmonologist",
            "skin": "Dermatologist",
            "joint": "Orthopedic",
            "stomach": "Gastroenterologist",
            "headache": "Neurologist"
        }
        
        # Check conditions first
        for condition in conditions:
            if condition.lower() in condition_map:
                return condition_map[condition.lower()]
        
        # Check symptoms
        for symptom in symptoms:
            for key, specialty in condition_map.items():
                if key in symptom.lower():
                    return specialty
        
        return "General Physician"
    
    def get_available_slots(self, specialty: str, days_ahead: int = 7) -> List[Dict]:
        """Get available appointment slots"""
        slots = []
        start_date = datetime.now() + timedelta(days=1)
        
        for day in range(days_ahead):
            date = start_date + timedelta(days=day)
            if date.weekday() < 5:  # Monday to Friday
                for hour in [9, 10, 11, 14, 15, 16, 17]:
                    slots.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "time": f"{hour:02d}:00",
                        "specialty": specialty,
                        "available": True
                    })
        
        return slots[:10]  # Return first 10 slots
    
    def format_booking_response(self, specialty: str, slots: List[Dict]) -> str:
        """Format booking information for user"""
        response = f"📅 **Appointment Booking - {specialty}**\n\n"
        response += "Available slots:\n\n"
        
        for i, slot in enumerate(slots[:5], 1):
            date_obj = datetime.strptime(slot['date'], "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            response += f"{i}. {day_name}, {slot['date']} at {slot['time']}\n"
        
        response += "\n📞 **To confirm your appointment:**\n"
        response += "1. Call Chronic Care: **1-800-CHRONIC** (1-800-247-6642)\n"
        response += "2. Visit: **https://chroniccare.com/book**\n"
        response += "3. Reply with the slot number you prefer\n\n"
        response += "💡 Please have your insurance information ready."
        
        return response
    
    def create_booking_link(self, specialty: str, date: str, time: str) -> str:
        """Generate booking link"""
        # In production, integrate with actual booking system
        base_url = "https://chroniccare.com/book"
        return f"{base_url}?specialty={specialty}&date={date}&time={time}"
