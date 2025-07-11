Strategy:
- Simple exchange arbitrage
- Use opening price of both exchanges as signal (if difference > threshold, run strategy)
- Search for all bids from one exchange that are higher then the offers from another
- Execute the minimum of bid volume or ask volume available

Assumptions:
- 1 second latency
- 10bps cost from BNC
- 20bps cost from HB
- Fill ratio 80%
- Threshold set at 1 s.d. (~0.006)

Summary of backtesting result:
==================================================
BACKTEST RESULTS (LINK/USDT Arbitrage)
==================================================
Metric                  Value   
Annualized Sharpe Ratio   -30.20
           Max Drawdown 21389.6%
               Win Rate      31%
Total PnL (After Costs)      $-0
==================================================

Post Trade Analysis:
- A jump in PnL around "2021-08-20 00:42:30" mark
- Sees >250 trades done around that time
- Strategy might be good at capturing dislocations
- Can further tweak strategy performance by changing the threshold
- Trading cost the largest impact on performance (need to reduce number of trades)
- Sees performance when threshold set higher (only trade on more significant signals)

Threshold at 0.002:
==================================================
BACKTEST RESULTS (LINK/USDT Arbitrage)
==================================================
Metric                  Value   
Annualized Sharpe Ratio    63.56
           Max Drawdown 43850.1%
               Win Rate      10%
Total PnL (After Costs)      $-4
==================================================

Threshold at 0.008:
==================================================
BACKTEST RESULTS (LINK/USDT Arbitrage)
==================================================
Metric                  Value 
Annualized Sharpe Ratio  47.17
           Max Drawdown 568.2%
               Win Rate    70%
Total PnL (After Costs)     $2
==================================================