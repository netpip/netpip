"""Tests for the grid rule."""

from pathlib import Path

from netpip.cli import main
from netpip.rules.grid import GridRule

SAMPLES = Path(__file__).parent / "samples"


def check(source):
    return GridRule().check(source)


def test_grid_without_limit_is_danger():
    findings = check("input int GridStep = 20;")
    assert len(findings) == 1
    assert findings[0].rule_id == "GRID_NO_LIMIT"
    assert findings[0].level == "DANGER"


def test_grid_with_limit_is_warning():
    findings = check("input int GridStep = 20;\ninput int MaxPositions = 5;")
    assert len(findings) == 1
    assert findings[0].rule_id == "GRID_WITH_LIMIT"
    assert findings[0].level == "WARNING"


def test_no_grid_gives_no_findings():
    assert check("input double Lot = 0.01;") == []


def test_grid_in_comment_is_ignored():
    assert check("// this is not a grid EA") == []


def test_limit_in_comment_does_not_count():
    findings = check("input int GridStep = 20;\n// MaxOrders = 5")
    assert findings[0].rule_id == "GRID_NO_LIMIT"


def test_grid_in_string_is_ignored():
    assert check('#property description "Grid bot"') == []


def test_cli_flags_grid_sample(capsys):
    main(["check", str(SAMPLES / "grid_bad.mq5")])
    out = capsys.readouterr().out
    assert "GRID_NO_LIMIT" in out
    assert "Risk score: 35/100 (MEDIUM)" in out
