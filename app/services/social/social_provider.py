from abc import ABC, abstractmethod

class SocialProvider(ABC):
    @abstractmethod
    def publish(self, text: str) -> str | None:
        """
        Publishes the given text to the platform.
        Returns the ID of the published post if successful, None otherwise.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the provider (e.g., 'twitter', 'threads').
        """
        pass
