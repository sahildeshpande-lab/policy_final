import re
from typing import Dict, List, Any, Optional, Tuple
from services.logging_service import logging_service

logger = logging_service.get_logger(__name__)

class ContextService:
    """Service for maintaining conversation context and understanding follow-up queries"""
    
    def __init__(self):
        self.context_keywords = {
            'wedding_leave': ['wedding', 'marriage', 'marry', 'getting married'],
            'sick_leave': ['sick', 'illness', 'medical', 'doctor', 'hospital'],
            'casual_leave': ['casual', 'personal', 'family'],
            'wfh': ['work from home', 'wfh', 'remote', 'home office'],
            'it_ticket': ['computer', 'laptop', 'printer', 'software', 'hardware', 'ticket'],
            'hr_policy': ['policy', 'policy', 'rules', 'regulations', 'hr', 'benefits']
        }
        
        self.follow_up_indicators = [
            'how', 'what', 'when', 'where', 'apply', 'process', 'procedure',
            'steps', 'requirements', 'documents', 'needed', 'eligible'
        ]
        
        self.reference_patterns = [
            r'(it|that|this|the).*leave',
            r'(it|that|this|the).*policy',
            r'(it|that|this|the).*process',
            r'(it|that|this|the).*application'
        ]

    def extract_context_from_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract context from conversation history"""
        context = {
            'current_topic': None,
            'last_intent': None,
            'entities_mentioned': [],
            'keywords_found': []
        }
        
        if not messages:
            return context
        
        # Get last few messages for context
        recent_messages = messages[-5:] if len(messages) >= 5 else messages
        
        for message in recent_messages:
            text = message.get('user_message', '').lower() + ' ' + message.get('assistant_message', '').lower()
            
            # Check for context keywords
            for topic, keywords in self.context_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        if topic not in context['keywords_found']:
                            context['keywords_found'].append(topic)
                        context['current_topic'] = topic
            
            # Extract specific entities
            if 'wedding' in text or 'marriage' in text:
                context['entities_mentioned'].append('wedding_leave')
            if 'sick' in text or 'medical' in text:
                context['entities_mentioned'].append('sick_leave')
            if 'casual' in text or 'personal' in text:
                context['entities_mentioned'].append('casual_leave')
        
        return context

    def is_follow_up_query(self, current_message: str, context: Dict[str, Any]) -> bool:
        """Check if current message is a follow-up to previous context"""
        message_lower = current_message.lower()
        
        # Check for follow-up indicators
        has_follow_up_indicator = any(indicator in message_lower for indicator in self.follow_up_indicators)
        
        # Check for reference patterns
        has_reference = any(re.search(pattern, message_lower) for pattern in self.reference_patterns)
        
        # Check if message is short (likely follow-up)
        is_short_message = len(current_message.split()) < 10
        
        # Check if there's active context
        has_active_context = context.get('current_topic') is not None
        
        return (has_follow_up_indicator or has_reference or is_short_message) and has_active_context

    def infer_intent_from_context(self, current_message: str, context: Dict[str, Any]) -> Tuple[str, float]:
        """Infer intent based on current message and conversation context"""
        message_lower = current_message.lower()
        
        # If there's clear follow-up intent, use the context topic
        if self.is_follow_up_query(current_message, context):
            current_topic = context.get('current_topic')
            if current_topic:
                if 'leave' in current_topic:
                    return 'leave', 0.9
                elif 'wfh' in current_topic:
                    return 'wfh', 0.9
                elif 'ticket' in current_topic:
                    return 'it_ticket', 0.9
                elif 'policy' in current_topic:
                    return 'hr_policy', 0.9
        
        # Check for explicit intent in current message
        if 'apply' in message_lower or 'application' in message_lower:
            if context.get('current_topic'):
                return context['current_topic'].replace('_leave', ''), 0.8
        
        return 'general_query', 0.3

    def get_contextual_response(self, current_message: str, context: Dict[str, Any]) -> Optional[str]:
        """Generate contextual response based on conversation history"""
        if not self.is_follow_up_query(current_message, context):
            return None
        
        current_topic = context.get('current_topic')
        message_lower = current_message.lower()
        
        if current_topic == 'wedding_leave':
            if any(word in message_lower for word in ['apply', 'application', 'process', 'how']):
                return "Based on our discussion about wedding leave, I can help you with the application process. Would you like to start the wedding leave application?"
            elif any(word in message_lower for word in ['eligible', 'requirements', 'documents']):
                return "For wedding leave eligibility, you typically need to provide marriage certificate and apply within a specific timeframe. Would you like me to start the application process or do you need more specific information?"
        
        elif current_topic == 'sick_leave':
            if any(word in message_lower for word in ['apply', 'application', 'process']):
                return "I can help you apply for sick leave. Would you like to start the sick leave application process?"
        
        elif current_topic == 'wfh':
            if any(word in message_lower for word in ['apply', 'application', 'request']):
                return "I can help you apply for work from home. Would you like to start the WFH application process?"
        
        return None

    def update_context_with_new_message(self, context: Dict[str, Any], message: str, intent: str):
        """Update context with new message information"""
        message_lower = message.lower()
        
        # Update current topic based on intent and message content
        if intent == 'leave':
            if 'wedding' in message_lower or 'marriage' in message_lower:
                context['current_topic'] = 'wedding_leave'
            elif 'sick' in message_lower or 'medical' in message_lower:
                context['current_topic'] = 'sick_leave'
            elif 'casual' in message_lower or 'personal' in message_lower:
                context['current_topic'] = 'casual_leave'
            else:
                context['current_topic'] = 'leave'
        elif intent == 'wfh':
            context['current_topic'] = 'wfh'
        elif intent == 'it_ticket':
            context['current_topic'] = 'it_ticket'
        elif intent == 'hr_policy':
            context['current_topic'] = 'hr_policy'
        
        context['last_intent'] = intent
