from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    @abstractmethod
    def fetch(self) -> list[dict]:
        """Return list of promo dicts with standard shape."""
        raise NotImplementedError
