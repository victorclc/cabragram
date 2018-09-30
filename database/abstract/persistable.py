from abc import ABC, abstractmethod


class PersistableObject(ABC):
    @abstractmethod
    def persistables(self):
        pass
