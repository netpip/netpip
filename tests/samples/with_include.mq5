// Test sample: pulls in local include files
#include "Include\risky.mqh"
#include "Include\absent.mqh"
#include <Trade\Trade.mqh>

void OnTick()
{
   trade.Buy(lot, _Symbol, ask, sl, tp);
}
