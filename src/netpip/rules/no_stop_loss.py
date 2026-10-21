"""Rule: detect orders opened without a stop loss."""

import re
from typing import List

from .base import Finding, Rule

# Matches trade.Buy( ... ) and trade.Sell( ... )
CALL = re.compile(r"\.(?:Buy|Sell)\s*\(")

# Literal values that mean "no stop loss"
ZERO_VALUES = {"0", "0.0", "0.00"}

IDENT = re.compile(r"^\w+$")

# Argument names that look like a stop loss or a take profit
SL_NAME = re.compile(r"(?i:stop_?loss)|(?:^|[a-z_\d])(?:SL|sl)(?:[A-Z_\d]|$)")
TP_NAME = re.compile(r"(?i:take_?profit)|(?:^|[a-z_\d])(?:TP|tp)(?:[A-Z_\d]|$)")

# Position of the stop loss in the standard CTrade signature:
# Buy(volume, symbol, price, sl, tp, comment)
DEFAULT_SL_INDEX = 3


def split_args(text: str) -> List[str]:
    """Split call arguments at top-level commas (ignores nested brackets)."""
    args, depth, current = [], 0, ""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            if depth == 0:
                break  # end of the call
            depth -= 1
        if ch == "," and depth == 0:
            args.append(current.strip())
            current = ""
        else:
            current += ch
    args.append(current.strip())
    return args


def stop_loss_index(args: List[str]) -> int:
    """Work out which argument is the stop loss."""
    for index, arg in enumerate(args):
        if IDENT.match(arg) and SL_NAME.search(arg):
            return index
    for index, arg in enumerate(args):
        if index > 0 and IDENT.match(arg) and TP_NAME.search(arg):
            return index - 1
    return DEFAULT_SL_INDEX


class NoStopLossRule(Rule):
    """Flags Buy/Sell calls where the stop loss argument is a literal 0."""

    id = "NO_STOP_LOSS"
    level = "DANGER"
    weight = 30
    message = "Order is opened without a stop loss (stop loss is 0)."

    def check(self, source: str) -> List[Finding]:
        findings = []
        for number, line in enumerate(source.splitlines(), start=1):
            code = line.split("//")[0]  # ignore comments
            match = CALL.search(code)
            if not match:
                continue
            args = split_args(code[match.end():])
            index = stop_loss_index(args)
            if index < len(args) and args[index] in ZERO_VALUES:
                findings.append(
                    Finding(self.id, self.level, self.message, number, self.weight)
                )
        return findings
