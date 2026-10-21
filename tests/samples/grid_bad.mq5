// Test sample: grid EA with no position limit
input int GridStep = 20;
input double Lot = 0.01;

void OnTick()
{
   if(PriceMovedAgainst(GridStep))
      trade.Buy(Lot, _Symbol, ask, sl, tp);
}
