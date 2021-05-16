"""Converts an epoch timestamp to a datetime object."""

from typing import Union
from datetime import datetime

def epoch_to_datetime(epoch: Union[int, float, str]) -> datetime:
    """Converts an epoch timestamp to a datetime object.

    Args:
        epoch - (int) Epoch time.
    
    Returns:
        datetime - Datetime equivalent of the epoch provided.
    """
    return datetime.fromtimestamp(float(epoch)/1000)
