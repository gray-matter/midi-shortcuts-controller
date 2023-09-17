from abc import ABCMeta, abstractmethod


class Focuser(metaclass=ABCMeta):
    @abstractmethod
    def focus(self):
        pass
