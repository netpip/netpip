"""Base classes for all netpip checking rules."""

from dataclasses import dataclass
from typing import List


@dataclass
class Finding:
    """A single result reported by a rule."""

    rule_id: str
    level: str      # "DANGER", "WARNING", or "INFO"
    message: str
    line: int       # line number in the file
    weight: int     # weight used to calculate the risk score
    file: str = ""  # which file the finding is in (set by the CLI)


class Rule:
    """Template for a rule. Every new rule inherits from this class."""

    id = ""
    level = "WARNING"
    weight = 0
    message = ""

    def check(self, source: str) -> List[Finding]:
        """Inspect the EA source code and return a list of findings."""
        raise NotImplementedError
