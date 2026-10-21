"""Tests for the stop loss input rule."""

from netpip.rules.stop_loss_input import StopLossInputRule


def check(source):
    return StopLossInputRule().check(source)


def test_flags_int_stop_loss_default_zero():
    assert len(check("input int StopLoss = 0;")) == 1


def test_flags_double_sl_default_zero():
    assert len(check("input double InpSL = 0.0;")) == 1


def test_ignores_nonzero_default():
    assert check("input int StopLoss = 400;") == []


def test_ignores_similar_names():
    source = "input bool SlopeDetection = false;\ninput int SlowMA = 0;"
    assert check(source) == []


def test_ignores_comments():
    assert check("// input int StopLoss = 0;") == []
