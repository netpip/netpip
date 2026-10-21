// Test sample: order opened without stop loss
void OnTick()
{
   trade.Sell(NormalizeDouble(lot, 2), _Symbol, bid, 0.0, tp);
}
