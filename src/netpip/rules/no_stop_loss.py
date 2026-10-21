"""Rule: detect orders opened without a stop loss."""

import re
from typing import List

from .base import Finding, Rule

# Matches CTrade calls such as trade.Buy( ... ) or trade.Sell( ... )
CALL = re.compile(r"\.(?:Buy|Sell)\s*\(")

# Literal values that mean "no stop loss"
ZERO_VALUES = {"0", "0.0", "0.00"}


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


class NoStopLossRule(Rule):
    """Flags CTrade Buy/Sell calls where the stop loss argument is 0."""

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
            # CTrade signature: Buy(volume, symbol, price, sl, tp, comment)
            args = split_args(code[match.end():])
            if len(args) >= 4 and args[3] in ZERO_VALUES:
                findings.append(
                    Finding(self.id, self.level, self.message, number, self.weight)
                )
        return findings
