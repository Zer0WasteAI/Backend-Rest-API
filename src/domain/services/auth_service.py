from abc import ABC, abstractmethod

class AuthService(ABC):
    @abstractmethod
    def create_tokens(self, identity: str) -> dict:
        """Creates a new set of tokens for the given identity."""
        pass

    @abstractmethod
    def decode_token(self, token: str) -> dict:
        """Decodes the given token and returns the payload."""
        pass
