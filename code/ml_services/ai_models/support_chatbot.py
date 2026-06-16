import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from transformers import pipeline

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    pipeline = None
    TRANSFORMERS_AVAILABLE = False

"\nAI Support Chatbot for Flowlet Developer Portal\nProvides intelligent assistance for developers integrating with the platform\n"
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries the chatbot can handle"""

    API_DOCUMENTATION = "api_documentation"
    INTEGRATION_HELP = "integration_help"
    TROUBLESHOOTING = "troubleshooting"
    BEST_PRACTICES = "best_practices"
    SECURITY_GUIDANCE = "security_guidance"
    COMPLIANCE_INFO = "compliance_info"
    GENERAL_INQUIRY = "general_inquiry"


class ConfidenceLevel(Enum):
    """Confidence levels for chatbot responses"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ChatMessage:
    """Represents a chat message"""

    id: str
    user_id: str
    message: str
    timestamp: datetime
    session_id: str
    context: Optional[Dict] = None


@dataclass
class ChatResponse:
    """Represents a chatbot response"""

    message_id: str
    response: str
    query_type: QueryType
    confidence: ConfidenceLevel
    suggested_actions: List[str]
    related_docs: List[str]
    escalate_to_human: bool
    processing_time_ms: int
    timestamp: datetime


class FlowletAIChatbot:
    """
    AI-powered chatbot for developer support
    Provides intelligent assistance for Flowlet platform integration
    """

    def __init__(self, knowledge_base_path: str = "/data/knowledge_base") -> None:
        self.knowledge_base_path = knowledge_base_path
        self.vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
        self.knowledge_vectors = None
        self.knowledge_documents = []
        self._initialize_models()
        self._load_knowledge_base()
        self.conversation_contexts = {}

    def _initialize_models(self) -> Any:
        """Initialize NLP models for intent classification and response generation"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning(
                "transformers not installed; NLP models disabled, "
                "falling back to TF-IDF similarity only"
            )
            self.intent_classifier = None
            self.qa_model = None
            return
        try:
            self.intent_classifier = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",
                return_all_scores=True,
            )
            self.qa_model = pipeline(
                "question-answering", model="distilbert-base-cased-distilled-squad"
            )
            logger.info("NLP models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing NLP models: {str(e)}")
            self.intent_classifier = None
            self.qa_model = None

    def _load_knowledge_base(self) -> Any:
        """Load and vectorize the knowledge base"""
        try:
            knowledge_files = [
                "api_documentation.json",
                "integration_guides.json",
                "troubleshooting_faq.json",
                "best_practices.json",
                "security_guidelines.json",
                "compliance_requirements.json",
            ]
            all_documents = []
            for file_name in knowledge_files:
                file_path = os.path.join(self.knowledge_base_path, file_name)
                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        documents = json.load(f)
                        all_documents.extend(documents)
                else:
                    self._create_sample_knowledge_base()
                    break
            if not all_documents:
                all_documents = self._get_default_knowledge_base()
            self.knowledge_documents = all_documents
            document_texts = [doc["content"] for doc in all_documents]
            self.knowledge_vectors = self.vectorizer.fit_transform(document_texts)
            logger.info(f"Knowledge base loaded with {len(all_documents)} documents")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {str(e)}")
            self.knowledge_documents = self._get_default_knowledge_base()

    def _create_sample_knowledge_base(self) -> Any:
        """Create sample knowledge base files"""
        os.makedirs(self.knowledge_base_path, exist_ok=True)
        sample_data = {
            "api_documentation.json": [
                {
                    "id": "api_001",
                    "title": "Wallet API Overview",
                    "content": "The Wallet API allows you to create and manage digital wallets. Use POST /v1/wallets to create a new wallet with required fields: type, ownerId, and currency.",
                    "category": "api",
                    "tags": ["wallet", "api", "create"],
                },
                {
                    "id": "api_002",
                    "title": "Payment Processing",
                    "content": "Process payments using POST /v1/payments endpoint. Required fields include sourceWalletId, amount, currency, and description.",
                    "category": "api",
                    "tags": ["payment", "api", "processing"],
                },
            ],
            "integration_guides.json": [
                {
                    "id": "guide_001",
                    "title": "Getting Started with Flowlet SDK",
                    "content": "Install the Flowlet SDK using npm install @flowlet/sdk. Initialize with your API key and environment configuration.",
                    "category": "integration",
                    "tags": ["sdk", "setup", "getting-started"],
                }
            ],
            "troubleshooting_faq.json": [
                {
                    "id": "faq_001",
                    "title": "Authentication Errors",
                    "content": "If you receive 401 authentication errors, verify your API key is correct and has the necessary permissions.",
                    "category": "troubleshooting",
                    "tags": ["authentication", "error", "401"],
                }
            ],
        }
        for filename, data in sample_data.items():
            with open(os.path.join(self.knowledge_base_path, filename), "w") as f:
                json.dump(data, f, indent=2)

    def _get_default_knowledge_base(self) -> List[Dict]:
        """Get default knowledge base if files are not available"""
        return [
            {
                "id": "default_001",
                "title": "Flowlet Platform Overview",
                "content": "Flowlet is an embedded finance platform that provides digital wallets, payment processing, card issuance, and compliance services through a comprehensive API.",
                "category": "general",
                "tags": ["overview", "platform"],
            },
            {
                "id": "default_002",
                "title": "API Authentication",
                "content": "All API requests require authentication using API keys. Include your API key in the Authorization header as 'Bearer YOUR_API_KEY'.",
                "category": "security",
                "tags": ["authentication", "api-key", "security"],
            },
        ]

    async def process_message(self, message: ChatMessage) -> ChatResponse:
        """Process incoming chat message and generate response"""
        start_time = datetime.now()
        try:
            query_type = await self._classify_intent(message.message)
            relevant_docs = await self._find_relevant_documents(message.message)
            response_text, confidence = await self._generate_response(
                message.message, query_type, relevant_docs
            )
            escalate_to_human = (
                confidence == ConfidenceLevel.LOW
                or "escalate" in message.message.lower()
            )
            suggested_actions = await self._generate_suggested_actions(
                query_type, relevant_docs
            )
            related_docs = [doc["title"] for doc in relevant_docs[:3]]
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            response = ChatResponse(
                message_id=f"resp_{message.id}",
                response=response_text,
                query_type=query_type,
                confidence=confidence,
                suggested_actions=suggested_actions,
                related_docs=related_docs,
                escalate_to_human=escalate_to_human,
                processing_time_ms=processing_time,
                timestamp=datetime.now(timezone.utc),
            )
            await self._update_conversation_context(message, response)
            await self._log_interaction(message, response)
            return response
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return self._generate_error_response(message, start_time)

    async def _classify_intent(self, message: str) -> QueryType:
        """Classify the intent of the user message"""
        try:
            if self.intent_classifier:
                pass
            message_lower = message.lower()
            if any(
                (
                    word in message_lower
                    for word in ["api", "endpoint", "request", "response"]
                )
            ):
                return QueryType.API_DOCUMENTATION
            elif any(
                (
                    word in message_lower
                    for word in ["integrate", "sdk", "setup", "install"]
                )
            ):
                return QueryType.INTEGRATION_HELP
            elif any(
                (
                    word in message_lower
                    for word in ["error", "bug", "issue", "problem", "fix"]
                )
            ):
                return QueryType.TROUBLESHOOTING
            elif any(
                (
                    word in message_lower
                    for word in ["best practice", "recommend", "should", "better"]
                )
            ):
                return QueryType.BEST_PRACTICES
            elif any(
                (
                    word in message_lower
                    for word in ["security", "secure", "encrypt", "auth"]
                )
            ):
                return QueryType.SECURITY_GUIDANCE
            elif any(
                (
                    word in message_lower
                    for word in ["compliance", "regulation", "kyc", "aml"]
                )
            ):
                return QueryType.COMPLIANCE_INFO
            else:
                return QueryType.GENERAL_INQUIRY
        except Exception as e:
            logger.error(f"Error classifying intent: {str(e)}")
            return QueryType.GENERAL_INQUIRY

    async def _find_relevant_documents(self, query: str, top_k: int = 5) -> List[Dict]:
        """Find relevant documents from knowledge base"""
        try:
            if self.knowledge_vectors is None:
                return []
            query_vector = self.vectorizer.transform([query])
            similarity_scores = cosine_similarity(
                query_vector, self.knowledge_vectors
            ).flatten()
            top_indices = np.argsort(similarity_scores)[::-1][:top_k]
            relevant_docs = []
            for idx in top_indices:
                if similarity_scores[idx] > 0.1:
                    doc = self.knowledge_documents[idx].copy()
                    doc["similarity_score"] = float(similarity_scores[idx])
                    relevant_docs.append(doc)
            return relevant_docs
        except Exception as e:
            logger.error(f"Error finding relevant documents: {str(e)}")
            return []

    async def _generate_response(
        self, query: str, query_type: QueryType, relevant_docs: List[Dict]
    ) -> Tuple[str, ConfidenceLevel]:
        """Generate response based on query and relevant documents"""
        try:
            if not relevant_docs:
                return (
                    self._generate_fallback_response(query_type),
                    ConfidenceLevel.LOW,
                )
            best_doc = relevant_docs[0]
            if query_type == QueryType.API_DOCUMENTATION:
                response = f"Based on our API documentation: {best_doc['content']}\n\n"
                response += "For more detailed information, please refer to our complete API documentation."
                confidence = (
                    ConfidenceLevel.HIGH
                    if best_doc["similarity_score"] > 0.7
                    else ConfidenceLevel.MEDIUM
                )
            elif query_type == QueryType.TROUBLESHOOTING:
                response = (
                    f"Here's how to resolve this issue: {best_doc['content']}\n\n"
                )
                response += "If this doesn't solve your problem, please provide more details about your specific situation."
                confidence = (
                    ConfidenceLevel.HIGH
                    if best_doc["similarity_score"] > 0.6
                    else ConfidenceLevel.MEDIUM
                )
            elif query_type == QueryType.INTEGRATION_HELP:
                response = f"For integration guidance: {best_doc['content']}\n\n"
                response += "Check out our integration examples and SDK documentation for step-by-step instructions."
                confidence = (
                    ConfidenceLevel.HIGH
                    if best_doc["similarity_score"] > 0.6
                    else ConfidenceLevel.MEDIUM
                )
            else:
                response = f"{best_doc['content']}\n\n"
                response += "Let me know if you need more specific information about this topic."
                confidence = ConfidenceLevel.MEDIUM
            return (response, confidence)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return (self._generate_fallback_response(query_type), ConfidenceLevel.LOW)

    def _generate_fallback_response(self, query_type: QueryType) -> str:
        """Generate fallback response when no relevant documents found"""
        fallback_responses = {
            QueryType.API_DOCUMENTATION: "I'd be happy to help with API documentation. Could you please specify which API endpoint or functionality you're interested in?",
            QueryType.INTEGRATION_HELP: "I can assist with integration questions. What specific part of the integration process are you working on?",
            QueryType.TROUBLESHOOTING: "I'm here to help troubleshoot issues. Could you provide more details about the error or problem you're experiencing?",
            QueryType.BEST_PRACTICES: "I can share best practices for using Flowlet. What specific area would you like guidance on?",
            QueryType.SECURITY_GUIDANCE: "Security is important! What specific security aspect of Flowlet would you like to know about?",
            QueryType.COMPLIANCE_INFO: "I can help with compliance information. Which regulatory requirements are you interested in?",
            QueryType.GENERAL_INQUIRY: "I'm here to help with any questions about Flowlet. Could you provide more details about what you're looking for?",
        }
        return fallback_responses.get(
            query_type,
            "I'm here to help! Could you please provide more details about your question?",
        )

    async def _generate_suggested_actions(
        self, query_type: QueryType, relevant_docs: List[Dict]
    ) -> List[str]:
        """Generate suggested actions based on query type and context"""
        base_actions = {
            QueryType.API_DOCUMENTATION: [
                "View complete API documentation",
                "Try the API in our sandbox",
                "Download SDK examples",
            ],
            QueryType.INTEGRATION_HELP: [
                "Follow our quick start guide",
                "Download SDK for your language",
                "Join our developer community",
            ],
            QueryType.TROUBLESHOOTING: [
                "Check system status",
                "Review error codes documentation",
                "Contact technical support",
            ],
            QueryType.BEST_PRACTICES: [
                "Read implementation guidelines",
                "Review security best practices",
                "Explore example applications",
            ],
            QueryType.SECURITY_GUIDANCE: [
                "Review security documentation",
                "Implement recommended security measures",
                "Schedule security consultation",
            ],
            QueryType.COMPLIANCE_INFO: [
                "Download compliance guides",
                "Review regulatory requirements",
                "Contact compliance team",
            ],
            QueryType.GENERAL_INQUIRY: [
                "Explore platform overview",
                "Schedule demo session",
                "Contact sales team",
            ],
        }
        return base_actions.get(query_type, ["Contact support team"])

    async def _update_conversation_context(
        self, message: ChatMessage, response: ChatResponse
    ):
        """Update conversation context for better continuity"""
        try:
            if message.session_id not in self.conversation_contexts:
                self.conversation_contexts[message.session_id] = {
                    "messages": [],
                    "topics": set(),
                    "last_query_type": None,
                }
            context = self.conversation_contexts[message.session_id]
            context["messages"].append(
                {
                    "user_message": message.message,
                    "bot_response": response.response,
                    "timestamp": message.timestamp.isoformat(),
                    "query_type": response.query_type.value,
                }
            )
            context["messages"] = context["messages"][-10:]
            if response.related_docs:
                context["topics"].update(response.related_docs)
            context["last_query_type"] = response.query_type
        except Exception as e:
            logger.error(f"Error updating conversation context: {str(e)}")

    async def _log_interaction(self, message: ChatMessage, response: ChatResponse):
        """Log interaction for analytics and improvement"""
        try:
            log_entry = {
                "timestamp": message.timestamp.isoformat(),
                "user_id": message.user_id,
                "session_id": message.session_id,
                "query": message.message,
                "query_type": response.query_type.value,
                "confidence": response.confidence.value,
                "processing_time_ms": response.processing_time_ms,
                "escalated": response.escalate_to_human,
            }
            logger.info(f"Chatbot interaction: {json.dumps(log_entry)}")
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")

    def _generate_error_response(
        self, message: ChatMessage, start_time: datetime
    ) -> ChatResponse:
        """Generate error response when processing fails"""
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        return ChatResponse(
            message_id=f"resp_{message.id}",
            response="I apologize, but I'm experiencing technical difficulties. Please try again or contact our support team for assistance.",
            query_type=QueryType.GENERAL_INQUIRY,
            confidence=ConfidenceLevel.LOW,
            suggested_actions=["Contact support team", "Try again later"],
            related_docs=[],
            escalate_to_human=True,
            processing_time_ms=processing_time,
            timestamp=datetime.now(timezone.utc),
        )


class ChatbotAnalytics:
    """Analytics and monitoring for chatbot performance"""

    def __init__(self) -> None:
        self.interaction_stats = {
            "total_interactions": 0,
            "by_query_type": {},
            "by_confidence": {},
            "escalation_rate": 0.0,
            "avg_processing_time": 0.0,
        }

    def update_stats(self, response: ChatResponse) -> Any:
        """Update analytics statistics"""
        self.interaction_stats["total_interactions"] += 1
        query_type = response.query_type.value
        if query_type not in self.interaction_stats["by_query_type"]:
            self.interaction_stats["by_query_type"][query_type] = 0
        self.interaction_stats["by_query_type"][query_type] += 1
        confidence = response.confidence.value
        if confidence not in self.interaction_stats["by_confidence"]:
            self.interaction_stats["by_confidence"][confidence] = 0
        self.interaction_stats["by_confidence"][confidence] += 1
        if response.escalate_to_human:
            escalations = sum(
                (
                    1
                    for qt, count in self.interaction_stats["by_query_type"].items()
                    if "escalated" in qt
                )
            )
            self.interaction_stats["escalation_rate"] = (
                escalations / self.interaction_stats["total_interactions"]
            )
        current_avg = self.interaction_stats["avg_processing_time"]
        new_avg = (
            current_avg * (self.interaction_stats["total_interactions"] - 1)
            + response.processing_time_ms
        ) / self.interaction_stats["total_interactions"]
        self.interaction_stats["avg_processing_time"] = new_avg

    def get_performance_report(self) -> Dict:
        """Get performance analytics report"""
        return self.interaction_stats.copy()


__all__ = [
    "FlowletAIChatbot",
    "ChatMessage",
    "ChatResponse",
    "QueryType",
    "ConfidenceLevel",
    "ChatbotAnalytics",
]
