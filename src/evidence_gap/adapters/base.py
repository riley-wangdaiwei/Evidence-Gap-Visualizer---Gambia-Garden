from abc import ABC, abstractmethod
class Adapter(ABC):
    @abstractmethod
    def read(self, path): ...
