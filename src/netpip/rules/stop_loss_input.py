"""Rule: detect stop loss inputs whose default value is 0."""

import re
from typing import List

from .base import Finding, Rule

INPUT = re.compile(
    r"^\s*input\s+(?:int|uint|long|ulong|double|float)\s+(\w+)\s*=\s*(0(?:\.0+)?)\s*;"
)

# Names like StopLoss, stop_loss, SL, SL_Points, InpSL, sl_pips.
# Names like SlopeDetection or SlowMA do not match.
SL_NAME = re.compile(r"(?i:stop_?loss)|(?:^|[a-z_\d])(?:SL|sl)(?:[A-Z_\d]|$)")


class StopLossInputRule(Rule):
    """Flags stop loss inputs that default to 0 (no stop loss)."""

    id = "SL_INPUT_ZERO"
    level = "WARNING"
    weight = 20
    message = (
        "A stop loss input defaults to 0, so orders may be opened without "
        "a stop loss unless the user sets a value."
    )

    def check(self, source: str) -> List[Finding]:
        findings = []
        for number, line in enumerate(source.splitlines(), start=1):
            code = line.split("//")[0]  # ignore comments
            match = INPUT.match(code)
            if match and SL_NAME.search(match.group(1)):
                findings.append(
                    Finding(self.id, self.level, self.message, number, self.weight)
                )
        return findings
