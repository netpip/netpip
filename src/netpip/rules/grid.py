"""Rule: detect grid-style EAs and whether they limit open positions."""

import re
from typing import List

from .base import Finding, Rule

STRING = re.compile(r'"[^"]*"')
GRID_WORD = re.compile(r"(?i)grid")
LIMIT_NAME = re.compile(
    r"(?i)max_?(?:orders?|positions?|trades?|levels?|baskets?|open\w*|grid\w*)"
    r"|(?:orders?|positions?|trades?|levels?)_?(?:limit|max)"
)


def clean(line: str) -> str:
    """Remove string literals and comments from one line of code."""
    return STRING.sub('""', line).split("//")[0]


class GridRule(Rule):
    """Flags grid-style EAs, and whether a position limit was found."""

    id = "GRID_NO_LIMIT"
    level = "DANGER"
    weight = 35
    message = (
        "Grid pattern found and no limit on open positions was found. "
        "In a strong trend, positions can keep piling up."
    )

    LIMITED_ID = "GRID_WITH_LIMIT"
    LIMITED_LEVEL = "WARNING"
    LIMITED_WEIGHT = 15
    LIMITED_MESSAGE = (
        "Grid pattern found. A position limit exists, but check that it is "
        "actually enforced before opening new orders."
    )

    def check(self, source: str) -> List[Finding]:
        grid_line = None
        has_limit = False
        for number, line in enumerate(source.splitlines(), start=1):
            code = clean(line)
            if grid_line is None and GRID_WORD.search(code):
                grid_line = number
            if LIMIT_NAME.search(code):
                has_limit = True
        if grid_line is None:
            return []
        if has_limit:
            return [
                Finding(
                    self.LIMITED_ID,
                    self.LIMITED_LEVEL,
                    self.LIMITED_MESSAGE,
                    grid_line,
                    self.LIMITED_WEIGHT,
                )
            ]
        return [Finding(self.id, self.level, self.message, grid_line, self.weight)]
