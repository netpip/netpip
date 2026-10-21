"""Rule: detect EAs that talk to the internet via WebRequest."""

import re
from typing import List

from .base import Finding, Rule

CALL = re.compile(r"\bWebRequest\s*\(")


class WebRequestRule(Rule):
    """Flags WebRequest calls, which send or receive data over the internet."""

    id = "WEBREQUEST"
    level = "WARNING"
    weight = 15
    message = (
        "EA uses WebRequest and can send or receive data over the internet. "
        "Check which URL it contacts and what data it sends."
    )

    def check(self, source: str) -> List[Finding]:
        findings = []
        for number, line in enumerate(source.splitlines(), start=1):
            code = line.split("//")[0]  # ignore comments
            if CALL.search(code):
                findings.append(
                    Finding(self.id, self.level, self.message, number, self.weight)
                )
        return findings
