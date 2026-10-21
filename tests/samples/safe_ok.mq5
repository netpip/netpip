// Test sample: fixed lot size
double lot = 0.01;

void OnTick()
{
   trade.Buy(lot, _Symbol, ask, sl, tp);
}
