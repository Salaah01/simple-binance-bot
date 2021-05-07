"""Interface declares operations common to all strategies."""

from typing import List, Optional, Callable, Union
from abc import ABC, abstractmethod
import numpy as np


class Strategy(ABC):
    """Interface declares operations common to all strategies."""

    def __init__(self, logFn: Optional[Callable] = None):
        """Sets up the log function, otherwise falls back to the default
        logging behaviour - to print to stdout.

        Args:
            logFn - (Callable) Logging function.
        """
        self.log(logFn)

    @property
    def log(self):
        return self._log

    @log.setter
    def log(self, logFn: Union[Callable, None]) -> None:
        """Checks if a logger has been provided, if not, defaults the logger
        behaviour to print any logging messages.

        Args:
            logFn - (Callable|None) Current logging function
        """
        if not logFn:
            self._log = lambda msg: print(msg)
        else:
            self._log = logFn

    @abstractmethod
    def apply_indicator(self, closePrices: np.array) -> dict:
        """Abstract method where the indicator/strategy would be implemented.

        Args:
            closePrices - (np.array) Collection of closing prices.

        Returns:
            A dictionary containing a `results` and `decision` key.
            `results` - (dict) Key = result name, value = result value.
            `decision` - 1 = buy, 0 = do nothing, 0 = sell.
        """
