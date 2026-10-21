// Test sample: contains a martingale pattern
double lot = 0.01;

void OnTick()
{
   if(lastTradeLoss)
      lot *= 2;
   trade.Buy(lot, _Symbol, ask, 0, tp);
}
