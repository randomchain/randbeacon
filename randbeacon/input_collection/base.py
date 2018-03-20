from abc import ABC, abstractmethod, abstractproperty

class BaseInputCollector(ABC):

    @abstractproperty
    def collected_inputs(self):
        yield None
