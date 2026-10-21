"""Rule: detect martingale-style lot multiplication."""

import re
from typing import List

from .base import Finding, Rule


class MartingaleRule(Rule):
    """Flags code that multiplies the lot size (a common martingale pattern)."""

    id = "MARTINGALE"
    level = "DANGER"
    weight = 40
    message = "Possible martingale: lot size is multiplied (often after a loss)."

    PATTERNS = [
        # lot *= 2;   currentLot *= multiplier;
        re.compile(r"\w*(?:lot|volume)\w*\s*\*=\s*[\w.]+", re.IGNORECASE),
        # lot = lot * 2;
        re.compile(
            r"\w*(?:lot|volume)\w*\s*=\s*\w*(?:lot|volume)\w*\s*\*\s*[\w.]+",
            re.IGNORECASE,
        ),
    ]

    def check(self, source: str) -> List[Finding]:
        findings = []
        for number, line in enumerate(source.splitlines(), start=1):
            code = line.split("//")[0]  # ignore comments
            if any(pattern.search(code) for pattern in self.PATTERNS):
                findings.append(
                    Finding(self.id, self.level, self.message, number, self.weight)
                )
        return findings
