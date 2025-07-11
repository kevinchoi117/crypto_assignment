'''
1. Design an arbitrage strategy on LINK/USDT between Binance and Huobi based on provided data.
2. Code a backtesting program by yourself with Python to test your strategy. Open source backtesting framework is not allowed.
3. Present your backtest result with risk metrics and charts.
4. Submit your risk metrics, charts, trade logs with backtesting Python script.
5. Post trade analysis will be a plus.

* Bar data and orderbook data of a 2 hours period are attached.
* BNC means data from Binance and HB means data from Huobi.
* In bar data file, we only keep 1s bar with trades happened.
* In orderbook data file, a1 means ask1 price, av1 means ask1 volume, b1 means bid1 price and bv1 means bid1 volume.
'''

import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

start_time = time.time()

'''
Data Processing
'''

bar_bnc = pd.read_csv('bar_bnc.csv')
bar_hb = pd.read_csv('bar_hb.csv')
ob_bnc = pd.read_csv('orderbook_bnc.csv')
ob_hb = pd.read_csv('orderbook_hb.csv')

bar_bnc = bar_bnc.set_index(['timestamp'])
bar_hb = bar_hb.set_index(['timestamp'])
ob_bnc = ob_bnc.set_index(['timestamp'])
ob_hb = ob_hb.set_index(['timestamp'])

merged_bar = pd.concat([bar_bnc.drop(columns='symbol'), bar_hb.drop(columns='symbol')], axis=1, keys=['LINKUSDT.BNC', 'LINKUSDT.HB'])
merged_ob = pd.concat([ob_bnc.drop(columns='symbol'), ob_hb.drop(columns='symbol')], axis=1, keys=['LINKUSDT.BNC', 'LINKUSDT.HB'])

'''
Arbitrage Signal

Notes:
Uses the differences in open price of exchanges as arbitrage signal
Signal follows a bell-curve distribution
Arbitrarily set threshold at 1 s.d (signals when differences between exchange open > 0.005)
Signal threshold used for reducing amount of transactions (lower cost))
'''

df_signal = merged_bar['LINKUSDT.BNC']['open'] - merged_bar['LINKUSDT.HB']['open']

# Generate histogram with header
print("\n" + "="*60)
print("PRICE DIFFERENCE DISTRIBUTION (LINK/USDT)")
print("="*60 + "\n")

ax = df_signal.hist(bins=100, 
                    figsize=(8, 4),
                    color='teal',
                    edgecolor='white',
                    grid=False)

ax.set_title('Distribution of Price Differences Between Exchanges', 
             pad=20, fontsize=14)
ax.set_xlabel('Price Difference (BNC - HB)', fontsize=12)
ax.set_ylabel('Frequency', fontsize=12)
ax.grid(axis='y', alpha=0.3)

mean_val = df_signal.mean()
std_val = df_signal.std()
ax.axvline(mean_val, color='red', linestyle='--', linewidth=1.5)
ax.axvline(mean_val + std_val, color='darkgreen', linestyle=':', linewidth=1)
ax.axvline(mean_val - std_val, color='darkgreen', linestyle=':', linewidth=1)

ax.legend([f'Mean: {mean_val:.6f}', 
           f'±1 Std Dev: {std_val:.6f}'])

plt.tight_layout()
plt.show()

signal_threshold = std_val #set threshold to be at 1 s.d.
#signal_threshold = 0.008

'''
Trade Strategy

Notes:
The strategys check for all the bid and ask price in order book
Hit all bids that are higher then ask
Order size is the minimum of b/a volume of order book from either exchange

Assumptions:
    Latency: 1s
    Trading cost on bnc: 10bps
    Trading cost on hb: 20bps
    Fill ratio: 80%

'''
    
latency_sec = 1
trading_cost_bps_bnc = 10  # 0.1%
trading_cost_bps_hb = 10   # 0.2%
fill_ratio = 0.8
trade_log = []

for ts in df_signal.index:

    ts_latency = datetime.strptime(ts, '%Y-%m-%d %H:%M:%S')
    ts_latency = ts_latency + timedelta(seconds = latency_sec)
    ts_latency = ts_latency.strftime('%Y-%m-%d %H:%M:%S')
    
    if ts_latency in merged_ob.index:
        if df_signal[ts] > signal_threshold:
            for i in range(10):
                if merged_ob['LINKUSDT.BNC']['b'+str(i+1)][ts_latency] > merged_ob['LINKUSDT.HB']['a'+str(i+1)][ts_latency]:
                    timestamp = ts_latency
                    ts_signal = ts
                    symbol = 'LINKUSDT.BNC'
                    action = 'SELL'
                    quantity = min(merged_ob['LINKUSDT.BNC']['bv'+str(i+1)][ts_latency], 
                                   merged_ob['LINKUSDT.HB']['av'+str(i+1)][ts_latency]) * fill_ratio
                    price = merged_ob['LINKUSDT.BNC']['b'+str(i+1)][ts_latency]
                    cost = price * trading_cost_bps_bnc * 0.0001
                    
                    trade = {'timestamp': timestamp, 'signal timestamp': ts_signal, 'symbol': symbol, 
                             'action': action,'quantity': quantity, 'price': price, 'cost': cost}
                    trade_log.append(trade)
                    
                    timestamp = ts_latency
                    symbol = 'LINKUSDT.HB'
                    action = 'BUY'
                    price = merged_ob['LINKUSDT.HB']['a'+str(i+1)][ts_latency]
                    cost = price * trading_cost_bps_hb * 0.0001
                    
                    trade = {'timestamp': timestamp, 'signal timestamp': ts_signal, 'symbol': symbol, 
                             'action': action,'quantity': quantity, 'price': price, 'cost': cost}
                    trade_log.append(trade)
    
        if df_signal[ts] < -signal_threshold:
            for i in range(10):                
                if merged_ob['LINKUSDT.HB']['b'+str(i+1)][ts_latency] > merged_ob['LINKUSDT.BNC']['a'+str(i+1)][ts_latency]:
                    timestamp = ts_latency
                    ts_signal = ts
                    symbol = 'LINKUSDT.HB'
                    action = 'SELL'
                    quantity = min(merged_ob['LINKUSDT.HB']['bv'+str(i+1)][ts_latency], merged_ob['LINKUSDT.BNC']['av'+str(i+1)][ts_latency])
                    price = merged_ob['LINKUSDT.HB']['b'+str(i+1)][ts_latency]
                    cost = price * trading_cost_bps_hb * 0.0001
                    
                    trade = {'timestamp': timestamp, 'signal timestamp': ts_signal, 'symbol': symbol, 
                             'action': action,'quantity': quantity, 'price': price, 'cost': cost}
                    trade_log.append(trade)
                    
                    timestamp = ts_latency
                    symbol = 'LINKUSDT.BNC'
                    action = 'BUY'
                    price = merged_ob['LINKUSDT.BNC']['a'+str(i+1)][ts_latency]
                    cost = price * trading_cost_bps_bnc * 0.0001
                    
                    trade = {'timestamp': timestamp, 'signal timestamp': ts_signal, 'symbol': symbol, 
                             'action': action,'quantity': quantity, 'price': price, 'cost': cost}
                    trade_log.append(trade)
                
'''
Risk Metrics:
PnL 
Sharpe Ratio
Max Drawdown
Win Rate

Notes:
Average of mid-price from HB and BNC are used as market mid for marking to market

'''

trade_log_df = pd.DataFrame(trade_log)
trade_log_df.to_csv('Trade_log.csv')

# Market mid to be used for MTM
df_MTM = (merged_ob['LINKUSDT.BNC']['b1'] + merged_ob['LINKUSDT.BNC']['a1'] 
          + merged_ob['LINKUSDT.HB']['b1'] + merged_ob['LINKUSDT.HB']['a1'])/4

# Cumulative PnL
def bs_mult(x):
    if x == 'BUY':
        return 1 
    elif x == 'SELL':
        return -1 
    
trade_log_df['mult'] = trade_log_df['action'].map(lambda x: bs_mult(x))
trade_log_df['quantity_action'] = trade_log_df['mult'] * trade_log_df['quantity']

pnl_log = []

for i in df_MTM.index:
    trade_log_filtered = trade_log_df[trade_log_df['timestamp'] < i].copy()
    trade_log_filtered['price_diff'] = df_MTM[i] - trade_log_filtered['price']
    trade_log_filtered['pnl'] = trade_log_filtered['price_diff'] * trade_log_df['quantity_action']
    pnl = sum(trade_log_filtered['pnl']) 
    pnl_w_cost = sum(trade_log_filtered['pnl']) - sum(trade_log_filtered['cost'])
    position = sum(trade_log_filtered['quantity_action'])
    
    pnl = {'timestamp': i, 'PnL': pnl, 'PnL w/ cost': pnl_w_cost, 'Position':position}
    pnl_log.append(pnl)

df_pnl_log = pd.DataFrame(pnl_log)
df_pnl_log.set_index('timestamp', inplace = True)

total_pnl = df_pnl_log['PnL w/ cost'].iloc[-1]

# Sharpe Ratio (annualized)
returns = df_pnl_log['PnL w/ cost'].pct_change()
sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252 * 24 * 3600)  # Annualize for 1-second bars

# Max Drawdown
df_pnl_log['Peak'] = df_pnl_log['PnL w/ cost'].cummax()
df_pnl_log['Drawdown'] = (df_pnl_log['Peak'] - df_pnl_log['PnL w/ cost']) / df_pnl_log['Peak']
max_drawdown = df_pnl_log['Drawdown'].max()

# Win Rate
win_rate = len(df_pnl_log[df_pnl_log['PnL w/ cost'] > 0]) / len(df_pnl_log)

'''
Chart 
Gross and Net PnL (w/ cost)
'''
from matplotlib.ticker import MaxNLocator

# Generate chart header
print("\n" + "="*60)
print("CUMULATIVE PNL OVER TIME")
print("="*60 + "\n")

# Create figure
plt.figure(figsize=(12, 6))

# Plot both PnL series
plt.plot(df_pnl_log.index, df_pnl_log['PnL'], 
         label='Gross PnL', color='#1f77b4', alpha=0.7, linewidth=1.5)
plt.plot(df_pnl_log.index, df_pnl_log['PnL w/ cost'], 
         label='Net PnL (w/ costs)', color='#ff7f0e', linewidth=2)

# Formatting
plt.title('Cumulative PnL Over Time', pad=20)
plt.ylabel('PnL (USD)')
plt.grid(True, alpha=0.3)
plt.legend(loc='upper left')

# Smart time axis formatting
ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(nbins=6))

# Add value markers
max_pnl = df_pnl_log['PnL w/ cost'].max()
min_pnl = df_pnl_log['PnL w/ cost'].min()
plt.annotate(f'Max: ${max_pnl:,.0f}', 
             xy=(df_pnl_log['PnL w/ cost'].idxmax(), max_pnl),
             xytext=(10,10), textcoords='offset points',
             arrowprops=dict(arrowstyle='->'))
plt.annotate(f'Min: ${min_pnl:,.0f}', 
             xy=(df_pnl_log['PnL w/ cost'].idxmin(), min_pnl),
             xytext=(10,-20), textcoords='offset points',
             arrowprops=dict(arrowstyle='->'))

# Tight layout
plt.tight_layout()
plt.savefig('cumulative_pnl.png', dpi=300, bbox_inches='tight')
plt.show()

'''
Results Summary
'''
results = {
    "Annualized Sharpe Ratio": f"{sharpe_ratio:.2f}",
    "Max Drawdown": f"{max_drawdown:.1%}",
    "Win Rate": f"{win_rate:.0%}",
    "Total PnL (After Costs)": f"${total_pnl:,.0f}"
}

results_df = pd.DataFrame(list(results.items()), 
                          columns=['Metric', 'Value'])

print("\n" + "="*50)
print("BACKTEST RESULTS (LINK/USDT Arbitrage)")
print("="*50)
print(results_df.to_string(index=False, justify='left'))
print("="*50)


end_time = time.time()
print(f"Execution time: {end_time - start_time:.4f} seconds")

'''
Post-trade analysis
'''
# Give ID to each pair of trade
x = []
for i in range(int(len(trade_log_df)/2)):
    x.append(i+1)
    x.append(i+1)

trade_log_df['trade_pair'] = x

# Calculate gross amount of each trade (need to multiply by -1 to flip direction)
trade_log_df['price_q'] = trade_log_df['price'] * trade_log_df['quantity_action'] * -1

# Calculate the PnL of each pair of trade
post_trd_df = trade_log_df.pivot(index = 'trade_pair', columns = 'symbol', values = 'price_q')
post_trd_df.columns = ['BNC', 'HB']
post_trd_df['PnL/trd'] = post_trd_df['BNC'] + post_trd_df['HB']

# Look at top 5 best and worst performing trades
pnl_worst = list(post_trd_df.sort_values(by='PnL/trd', ascending = True).head(5).index)
pnl_best = list(post_trd_df.sort_values(by='PnL/trd', ascending = False).head(5).index)

def get_trade(ID):
    return trade_log_df[trade_log_df['trade_pair'] == ID]

# get_trade(208)

# Amount of trades by time
trade_log_df['timestamp'] = pd.to_datetime(trade_log_df['timestamp'])
trade_counts = trade_log_df.resample('1min', on='timestamp').size()
plt.figure(figsize=(12, 6))
trade_counts.plot(kind='bar', width=0.8, alpha=0.7, color='royalblue')
plt.title('Trade Count Over Time (1-Minute Bins)')
plt.xlabel('Timestamp')
plt.ylabel('Number of Trades')
plt.grid(axis='y', alpha=0.3)
plt.xticks(rotation=90)
plt.tight_layout()

ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(nbins=15))

plt.savefig('Trade count over time.png', dpi=300, bbox_inches='tight')
plt.show()