"""Tests for stop loss detection by argument name."""

from netpip.rules.no_stop_loss import NoStopLossRule


def check(source):
    return NoStopLossRule().check(source)


def test_wrapper_with_named_stop_loss_is_ok():
    assert check("trade.Buy(_Symbol, TradeVolume, StopLoss, TakeProfit);") == []


def test_wrapper_with_zero_stop_loss_is_flagged():
    assert len(check("trade.Buy(_Symbol, TradeVolume, 0, TakeProfit);")) == 1


def test_standard_ctrade_zero_stop_loss_is_flagged():
    assert len(check("trade.Sell(lot, _Symbol, bid, 0, tp);")) == 1


def test_standard_ctrade_with_stop_loss_is_ok():
    assert check("trade.Sell(lot, _Symbol, bid, sl, tp);") == []


def test_zero_take_profit_is_not_a_missing_stop_loss():
    assert check("trade.Buy(lot, _Symbol, ask, sl, 0);") == []
