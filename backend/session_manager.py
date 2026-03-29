"""Session manager for storing conversation history per session.

Uses an in-memory dict with TTL-based expiration for simplicity.
In production, you'd use Redis or a database.
"""

import time
import uuid
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class Session:
    """A conversation session with its history."""
    session_id: str
    conversation_history: list = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)


class SessionManager:
    """Thread-safe session storage with TTL expiration."""

    def __init__(self, ttl_seconds: float = 3600.0):
        """Initialize the session manager.

        Args:
            ttl_seconds: How long sessions live without access (default 1 hour).
        """
        self._sessions: dict[str, Session] = {}
        self._lock = Lock()
        self._ttl = ttl_seconds

    def create_session(self) -> Session:
        """Create a new session with a unique ID."""
        session_id = str(uuid.uuid4())
        session = Session(session_id=session_id)
        with self._lock:
            self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        """Get a session by ID, updating last_accessed time.

        Returns None if the session doesn't exist or has expired.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None

            # Check if expired
            if time.time() - session.last_accessed > self._ttl:
                del self._sessions[session_id]
                return None

            session.last_accessed = time.time()
            return session

    def get_or_create_session(self, session_id: str | None) -> Session:
        """Get an existing session or create a new one.

        Args:
            session_id: The session ID to look up, or None to create new.
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
        return self.create_session()

    def cleanup_expired(self) -> int:
        """Remove expired sessions. Returns count of removed sessions."""
        now = time.time()
        removed = 0
        with self._lock:
            expired_ids = [
                sid for sid, s in self._sessions.items()
                if now - s.last_accessed > self._ttl
            ]
            for sid in expired_ids:
                del self._sessions[sid]
                removed += 1
        return removed


# Global session manager instance
session_manager = SessionManager()
