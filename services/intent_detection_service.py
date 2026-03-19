import re
from typing import Dict, List, Optional, Tuple
from services.logging_service import logging_service

logger = logging_service.get_logger(__name__)

class IntentDetectionService:
    def __init__(self):
        self.intent_patterns = {
            "leave": [
                r"(?i)\b(apply|want|need|request).*leave\b",
                r"(?i)\bleave.*application\b",
                r"(?i)\b(casual|sick|planned).*leave\b",
                r"(?i)\btake.*leave\b",
                r"(?i)\bgo.*on.*leave\b",
                r"(?i)\bleave.*balance\b",
                r"(?i)\bapply.*for.*leave\b",
                r"(?i)\bwedding.*leave\b",
                r"(?i)\bmarriage.*leave\b",
                r"(?i)\bmaternity.*leave\b",
                r"(?i)\bpaternity.*leave\b",
                r"(?i)\bemergency.*leave\b",
                r"(?i)\bcompassionate.*leave\b",
                r"(?i)\bbereavement.*leave\b"
            ],
            "wfh": [
                r"(?i)\b(work.*from.*home|wfh)\b",
                r"(?i)\bapply.*wfh\b",
                r"(?i)\brequest.*wfh\b",
                r"(?i)\bwork.*remotely\b",
                r"(?i)\bhome.*office\b",
                r"(?i)\btelecommute\b"
            ],
            "it_ticket": [
                r"(?i)\b(it.*ticket|helpdesk|support)\b",
                r"(?i)\b(raise|create|submit).*ticket\b",
                r"(?i)\b(computer|laptop|system).*issue\b",
                r"(?i)\b(software|hardware).*problem\b",
                r"(?i)\binternet.*connection\b",
                r"(?i)\bprinter.*not.*working\b",
                r"(?i)\blogin.*issue\b",
                r"(?i)\bpassword.*reset\b"
            ],
            "hr_policy": [
                r"(?i)\b(hr|human.*resource)\b",
                r"(?i)\b(company.*policy|policies)\b",
                r"(?i)\b(employee.*handbook)\b",
                r"(?i)\b(work.*rules|regulations)\b",
                r"(?i)\b(benefits|compensation)\b",
                r"(?i)\b(performance.*review)\b",
                r"(?i)\b(code.*of.*conduct)\b"
            ],
            "general_query": [
                r"(?i)\b(how|what|when|where|why|who)\b",
                r"(?i)\b(help|assist|guide)\b",
                r"(?i)\b(information|details)\b",
                r"(?i)\b(explain|clarify)\b"
            ]
        }
        
        self.intent_mappings = {
            "leave": "Leave Apply",
            "wfh": "Apply WFH", 
            "it_ticket": "IT Ticket Raised",
            "hr_policy": "HR Related Instructions",
            "general_query": "Any Query"
        }
        
        self.intent_responses = {
            "leave": "I can help you apply for leave. We support various types including wedding leave, marriage leave, maternity/paternity leave, emergency leave, and compassionate leave. Would you like to start the leave application process?",
            "wfh": "I can help you apply for work from home. Would you like to start the WFH application process?",
            "it_ticket": "I can help you raise an IT support ticket. Would you like to start the IT ticket process?",
            "hr_policy": "I can help you with HR policies and company information. What specific policy would you like to know about?",
            "general_query": "I'm here to help with any questions you have. What would you like to know?"
        }

    def detect_intent(self, message: str) -> Tuple[str, float]:
        """Detect the primary intent from user message"""
        message = message.strip().lower()
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, message)
                score += len(matches)
                
                # Bonus for exact phrase matches
                if re.search(pattern, message):
                    score += 2
                    
            scores[intent] = score
        
        if not any(scores.values()):
            return "general_query", 0.0
            
        best_intent = max(scores, key=scores.get)
        confidence = min(scores[best_intent] / 5.0, 1.0)
        
        return best_intent, confidence

    def get_suggested_actions(self, intent: str, confidence: float) -> List[Dict]:
        """Get suggested action buttons based on detected intent"""
        if confidence < 0.3:
            return []
            
        action_type = self.intent_mappings.get(intent, "Any Query")
        
        if intent in ["leave", "wfh", "it_ticket"]:
            return [
                {
                    "type": action_type,
                    "label": f"Start {action_type}",
                    "action": "start_flow",
                    "confidence": confidence
                }
            ]
        elif intent == "hr_policy":
            return [
                {
                    "type": "HR Related Instructions", 
                    "label": "Ask about HR Policies",
                    "action": "category_select",
                    "confidence": confidence
                }
            ]
        
        return []

    def get_intent_response(self, intent: str) -> str:
        """Get contextual response for detected intent"""
        return self.intent_responses.get(intent, "How can I help you today?")

    def process_message(self, message: str) -> Dict:
        """Process message and return intent detection results"""
        intent, confidence = self.detect_intent(message)
        suggested_actions = self.get_suggested_actions(intent, confidence)
        response = self.get_intent_response(intent)
        
        return {
            "intent": intent,
            "confidence": confidence,
            "suggested_actions": suggested_actions,
            "response": response,
            "mapped_type": self.intent_mappings.get(intent, "Any Query")
        }
