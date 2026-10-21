"""Tests for netpip rules, the risk report, and the CLI."""

from pathlib import Path

from netpip.cli import main
from netpip.report import risk_label, risk_score
from netpip.rules.base import Finding
from netpip.rules.martingale import MartingaleRule
from netpip.rules.no_stop_loss import NoStopLossRule
from netpip.rules.webrequest import WebRequestRule

SAMPLES = Path(__file__).parent / "samples"


def read(name):
    return (SAMPLES / name).read_text(encoding="utf-8")


# --- Martingale rule ---

def test_martingale_detects_lot_multiplication():
    findings = MartingaleRule().check(read("martingale_bad.mq5"))
    assert len(findings) == 1
    assert findings[0].line == 7


def test_martingale_ignores_fixed_lot():
    assert MartingaleRule().check(read("safe_ok.mq5")) == []


def test_martingale_ignores_comments():
    assert MartingaleRule().check("// lot *= 2;") == []


# --- No stop loss rule ---

def test_no_stop_loss_detects_zero_sl():
    findings = NoStopLossRule().check(read("no_sl_bad.mq5"))
    assert len(findings) == 1
    assert findings[0].line == 4


def test_no_stop_loss_accepts_real_stop_loss():
    assert NoStopLossRule().check(read("safe_ok.mq5")) == []


def test_no_stop_loss_handles_nested_brackets():
    source = "trade.Buy(NormalizeDouble(lot, 2), _Symbol, ask, sl, tp);"
    assert NoStopLossRule().check(source) == []


# --- WebRequest rule ---

def test_webrequest_detects_call():
    findings = WebRequestRule().check(read("webrequest_bad.mq5"))
    assert len(findings) == 1


def test_webrequest_ignores_safe_file():
    assert WebRequestRule().check(read("safe_ok.mq5")) == []


def test_webrequest_ignores_comments():
    assert WebRequestRule().check("// WebRequest(...) is not used") == []


# --- Risk score ---

def test_risk_score_counts_each_rule_once():
    findings = [
        Finding("A", "DANGER", "m", 1, 40),
        Finding("A", "DANGER", "m", 2, 40),
    ]
    assert risk_score(findings) == 40


def test_risk_score_is_capped_at_100():
    findings = [
        Finding("A", "DANGER", "m", 1, 60),
        Finding("B", "DANGER", "m", 2, 60),
    ]
    assert risk_score(findings) == 100


def test_risk_label_thresholds():
    assert risk_label(0) == "LOW"
    assert risk_label(30) == "MEDIUM"
    assert risk_label(60) == "HIGH"


# --- Command line ---

def test_cli_check_runs_on_sample(capsys):
    exit_code = main(["check", str(SAMPLES / "safe_ok.mq5")])
    assert exit_code == 0
    assert "Risk score: 0/100" in capsys.readouterr().out


def test_cli_reports_missing_file():
    assert main(["check", "does_not_exist.mq5"]) == 2
