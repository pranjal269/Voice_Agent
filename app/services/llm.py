"""Large Language Model service using Google Gemini."""

from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Try importing Gemini SDK
try:
    import google.generativeai as genai
    
    # Initialize Gemini if API key is available
    if settings.GEMINI_API_KEY:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            logger.info("Google Gemini LLM service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {str(e)}")
            genai = None
    else:
        logger.warning("Gemini API key not configured")
        genai = None
        
except ImportError:
    logger.error("google-generativeai package not installed")
    genai = None


class LLMService:
    """Large Language Model service using Google Gemini."""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.genai = genai
        
    def is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(self.api_key and self.genai)
    
    def generate_response(
        self,
        prompt: str,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        system_instruction: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a response using the LLM.
        
        Args:
            prompt: Input prompt for the model
            model: Model name to use
            temperature: Generation temperature
            system_instruction: System instruction for the model
            
        Returns:
            Generated response text, or None if failed
        """
        if not self.is_configured():
            logger.error("LLM service not configured")
            raise ValueError("LLM service not configured")
        
        try:
            logger.info(f"Generating LLM response with model {model}")
            logger.debug(f"Prompt: {prompt[:100]}...")
            
            # Create model instance
            model_instance = self.genai.GenerativeModel(model_name=model)
            
            # Prepare the full prompt with system instruction
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"System: {system_instruction}\n\nUser: {prompt}"
            
            # Generate response
            generation_config = {"temperature": temperature}
            result = model_instance.generate_content(full_prompt, generation_config=generation_config)
            
            # Extract response text
            response_text = self._extract_response_text(result)
            
            if not response_text:
                logger.error("LLM returned empty response")
                return None
            
            logger.info(f"LLM response generated: {len(response_text)} characters")
            logger.debug(f"Response: {response_text[:100]}...")
            
            return response_text
            
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            return None
    
    def generate_conversational_response(
        self,
        conversation_history: List[Dict[str, str]],
        model: str = "gemini-1.5-flash",
        temperature: float = 0.7
    ) -> Optional[str]:
        """
        Generate a response based on conversation history.
        
        Args:
            conversation_history: List of conversation messages
            model: Model name to use
            temperature: Generation temperature
            
        Returns:
            Generated response text, or None if failed
        """
        if not self.is_configured():
            logger.error("LLM service not configured")
            raise ValueError("LLM service not configured")
        
        try:
            # Build conversation context
            conversation_text = ""
            for msg in conversation_history:
                if msg["role"] == "user":
                    conversation_text += f"User: {msg['content']}\n"
                else:
                    conversation_text += f"Assistant: {msg['content']}\n"
            
            conversation_text += "Assistant:"
            
            logger.info(f"Generating conversational response for {len(conversation_history)} messages")
            
            # Create model instance
            model_instance = self.genai.GenerativeModel(model_name=model)
            
            # Add system instruction to conversation text
            full_conversation = "System: You are a helpful AI assistant. Respond naturally and remember the conversation context.\n\n" + conversation_text
            
            # Generate response
            generation_config = {"temperature": temperature}
            result = model_instance.generate_content(full_conversation, generation_config=generation_config)
            
            # Extract response text
            response_text = self._extract_response_text(result)
            
            if not response_text:
                logger.error("LLM returned empty conversational response")
                return None
            
            logger.info(f"Conversational response generated: {len(response_text)} characters")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Conversational LLM generation failed: {str(e)}")
            return None
    
    def _extract_response_text(self, result: Any) -> Optional[str]:
        """
        Extract response text from Gemini result object.
        
        Args:
            result: Result object from Gemini API
            
        Returns:
            Extracted text or None
        """
        try:
            # Try primary method
            response_text = getattr(result, "text", None)
            if response_text:
                return response_text.strip()
            
            # Fallback for different SDK versions
            candidates = getattr(result, "candidates", []) or []
            response_text = "\n".join(
                part.text
                for candidate in candidates
                for part in getattr(getattr(candidate, "content", {}), "parts", [])
                if hasattr(part, "text")
            )
            
            return response_text.strip() if response_text else None
            
        except Exception as e:
            logger.error(f"Failed to extract response text: {str(e)}")
            return None
    
    def get_error_type(self, error_message: str) -> str:
        """
        Determine error type from error message.
        
        Args:
            error_message: Error message string
            
        Returns:
            Error type classification
        """
        error_str = error_message.lower()
        
        if "quota" in error_str or "429" in error_str:
            return "LLM_QUOTA_ERROR"
        elif "api key" in error_str or "authentication" in error_str:
            return "LLM_AUTH_ERROR"
        elif "network" in error_str or "connection" in error_str or "timeout" in error_str:
            return "LLM_NETWORK_ERROR"
        else:
            return "LLM_GENERAL_ERROR"
    
    def get_fallback_message(self, error_type: str) -> str:
        """
        Get appropriate fallback message for error type.
        
        Args:
            error_type: Type of error that occurred
            
        Returns:
            Appropriate fallback message
        """
        fallback_messages = {
            "LLM_QUOTA_ERROR": "I've reached my daily conversation limit. Please try again tomorrow, or consider upgrading for unlimited conversations!",
            "LLM_AUTH_ERROR": "I'm having authentication issues right now. Please try again in a few moments.",
            "LLM_NETWORK_ERROR": "I'm having trouble connecting to my AI brain right now. Please try again in a moment!",
            "LLM_GENERAL_ERROR": "I'm experiencing some technical difficulties right now. Please try asking your question again!"
        }
        
        return fallback_messages.get(error_type, fallback_messages["LLM_GENERAL_ERROR"])


# Global LLM service instance
llm_service = LLMService()
