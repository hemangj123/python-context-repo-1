from auth.token_validator import TokenValidator


class SessionManager:
    """
    Manage user sessions

    """
    
    def __init__(self):
        self.validator = TokenValidator()
        self._sessions = {}
    
    def validate_session(self, token: str) -> bool:
        """
        Validate session token

        """
        return self.validator.validate(token)
    
    def create_session(self, user_id: str) -> str:
        """Create new session for user"""
        import uuid
        token = str(uuid.uuid4())
        self._sessions[token] = user_id
        return token
    
    def destroy_session(self, token: str) -> None:
        """Destroy session"""
        if token in self._sessions:
            del self._sessions[token]
