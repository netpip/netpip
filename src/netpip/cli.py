"""Command-line interface for netpip."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from . import __version__
from .report import format_report
from .rules import ALL_RULES


def read_source(path: Path) -> str:
    """Read an EA file. MetaEditor often saves files as UTF-16."""
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig", errors="replace")


def run_check(file_name: str) -> int:
    path = Path(file_name)
    if not path.is_file():
        print(f"Error: file not found: {file_name}", file=sys.stderr)
        return 2
    source = read_source(path)
    findings = []
    for rule_class in ALL_RULES:
        findings.extend(rule_class().check(source))
    findings.sort(key=lambda finding: finding.line)
    print(format_report(path.name, findings))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="netpip",
        description="Check and test MetaTrader 5 Expert Advisors.",
    )
    parser.add_argument("--version", action="version", version=f"netpip {__version__}")
    subcommands = parser.add_subparsers(dest="command")
    check = subcommands.add_parser(
        "check", help="check an EA source file for risky patterns"
    )
    check.add_argument("file", help="path to a .mq5 file")
    args = parser.parse_args(argv)
    if args.command == "check":
        return run_check(args.file)
    parser.print_help()
    return 0
