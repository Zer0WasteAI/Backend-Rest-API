from abc import ABC, abstractmethod

class OAuthService(ABC):
    @abstractmethod
    def get_user_info(self, code: str) -> dict:
        """
        Retrieve user information from the OAuth provider using the provided authorization code.

        :param code: The authorization code received from the OAuth provider.
        :return: A dictionary containing user information.
        """
        pass