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
        self._log = self._set_log(logFn)

    def log(self):
        return self._log

    def _set_log(self, logFn: Union[Callable, None]) -> None:
        """Checks if a logger has been provided, if not, defaults the logger
        behaviour to print any logging messages.

        Args:
            logFn - (Callable|None) Current logging function
        """
        if not logFn:
            def log(msg):
                return msg
            return log
        else:
            return logFn

    @abstractmethod
    def apply_indicator(
        self,
        closePrices: np.array,
        config: dict,
        coinsOwned: bool,
    ) -> dict:
        """Abstract method where the indicator/strategy would be implemented.

        Args:
            closePrices - (np.array) Collection of closing prices.
            config: - (dict) Configurations for the strategy.
            coinsOwned - (bool) Is the coined/currency owned?

        Returns:
            A dictionary containing a `results` and `decision` key.
            `results` - (dict) Key = result name, value = result value.
            `decision` - 1 = buy, 0 = do nothing, 0 = sell.
        """
