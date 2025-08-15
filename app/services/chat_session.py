"""Chat session management service."""

from typing import Dict, List, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatSessionManager:
    """Manages chat sessions and conversation history."""
    
    def __init__(self):
        # In-memory storage for chat history
        # Format: {session_id: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
        self._sessions: Dict[str, List[Dict[str, str]]] = {}
        logger.info("Chat session manager initialized")
    
    def get_session_history(self, session_id: str) -> List[Dict[str, str]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            List of conversation messages
        """
        return self._sessions.get(session_id, [])
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """
        Add a message to the session history.
        
        Args:
            session_id: Unique session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        if session_id not in self._sessions:
            self._sessions[session_id] = []
            logger.info(f"Created new chat session: {session_id}")
        
        self._sessions[session_id].append({
            "role": role,
            "content": content
        })
        
        logger.debug(f"Added {role} message to session {session_id}: {content[:50]}...")
    
    def get_message_count(self, session_id: str) -> int:
        """
        Get the number of messages in a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Number of messages in the session
        """
        return len(self._sessions.get(session_id, []))
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session was cleared, False if session didn't exist
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Cleared chat session: {session_id}")
            return True
        return False
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of active session IDs.
        
        Returns:
            List of active session IDs
        """
        return list(self._sessions.keys())
    
    def get_session_stats(self) -> Dict[str, int]:
        """
        Get statistics about active sessions.
        
        Returns:
            Dictionary with session statistics
        """
        total_sessions = len(self._sessions)
        total_messages = sum(len(history) for history in self._sessions.values())
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / total_sessions if total_sessions > 0 else 0
        }


# Global chat session manager instance
chat_manager = ChatSessionManager()
