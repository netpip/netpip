"""Format check results for the terminal."""

from typing import List, Optional

from .rules.base import Finding


def risk_score(findings: List[Finding]) -> int:
    """Sum the weight of each rule once, capped at 100."""
    weights = {}
    for finding in findings:
        weights[finding.rule_id] = finding.weight
    return min(100, sum(weights.values()))


def risk_label(score: int) -> str:
    if score >= 60:
        return "HIGH"
    if score >= 30:
        return "MEDIUM"
    return "LOW"


def format_report(
    filename: str,
    findings: List[Finding],
    missing: Optional[List[str]] = None,
    files_checked: int = 1,
) -> str:
    lines = [f"netpip check: {filename}", ""]
    if not findings:
        lines.append("No known warning signs were found.")
    for finding in findings:
        if finding.file and finding.file != filename:
            where = f"{finding.file}, line {finding.line}"
        else:
            where = f"line {finding.line}"
        lines.append(f"[{finding.level}] {where}: {finding.rule_id}")
        lines.append(f"    {finding.message}")
    score = risk_score(findings)
    lines.append("")
    lines.append(f"Files checked: {files_checked}")
    if missing:
        lines.append("Not analyzed (file not found next to the EA):")
        for name in missing:
            lines.append(f"  - {name}")
        lines.append("Risky code inside these files cannot be detected.")
    lines.append(f"Risk score: {score}/100 ({risk_label(score)})")
    lines.append("Note: this is a rule-based check. It cannot prove an EA is safe.")
    return "\n".join(lines)
