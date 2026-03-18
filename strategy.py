import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

def basic_strategy(ticker, short_window=20, long_window=60):
    # 1. 資料獲取：下載歷史股價 (以台積電 ADR 為例: TSM)
    df = yf.download(ticker, start="2023-01-01", end="2026-01-01")
    
    # 2. 策略計算：簡單移動平均線 (SMA)
    df['SMA_Short'] = df['Close'].rolling(window=short_window).mean()
    df['SMA_Long'] = df['Close'].rolling(window=long_window).mean()
    
    # 3. 產生訊號：黃金交叉買入 (1)，死亡交叉賣出 (-1)
    df['Signal'] = 0
    df.iloc[short_window:, df.columns.get_loc('Signal')] = \
        (df['SMA_Short'][short_window:] > df['SMA_Long'][short_window:]).astype(int)
    
    # 計算持倉變化 (1 代表買進訊號發生的瞬間)
    df['Position'] = df['Signal'].diff()
    
    return df

# 執行策略
data = basic_strategy('TSM')

# 4. 簡單視覺化
plt.figure(figsize=(12,6))
plt.plot(data['Close'], label='Price', alpha=0.5)
plt.plot(data['SMA_Short'], label='20-day SMA')
plt.plot(data['SMA_Long'], label='60-day SMA')
plt.title('Quant Strategy: SMA Crossover')
plt.legend()
plt.show()

print(data.tail(10))