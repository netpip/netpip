"""Rule registry. Add new rules to ALL_RULES."""

from .martingale import MartingaleRule
from .no_stop_loss import NoStopLossRule
from .stop_loss_input import StopLossInputRule
from .webrequest import WebRequestRule

ALL_RULES = [MartingaleRule, NoStopLossRule, StopLossInputRule, WebRequestRule]
