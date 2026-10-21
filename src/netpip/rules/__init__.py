"""Rule registry. Add new rules to ALL_RULES."""

from .grid import GridRule
from .martingale import MartingaleRule
from .no_stop_loss import NoStopLossRule
from .stop_loss_input import StopLossInputRule
from .webrequest import WebRequestRule

ALL_RULES = [
    GridRule,
    MartingaleRule,
    NoStopLossRule,
    StopLossInputRule,
    WebRequestRule,
]
