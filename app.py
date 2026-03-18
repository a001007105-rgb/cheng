import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ─── 頁面設定 ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SMA 均線策略分析",
    page_icon="📈",
    layout="wide"
)

st.title("📈 SMA 均線交叉策略分析工具")
st.markdown("使用簡單移動平均線（SMA）分析股票買賣訊號，支援黃金交叉與死亡交叉策略。")

# ─── 側邊欄參數設定 ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 參數設定")
    ticker = st.text_input("股票代號", value="TSM", help="範例：TSM、AAPL、0050.TW")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("開始日期", value=pd.Timestamp("2023-01-01"))
    with col2:
        end_date = st.date_input("結束日期", value=pd.Timestamp("2026-01-01"))
    short_window = st.slider("短期均線（天）", min_value=5, max_value=60, value=20)
    long_window = st.slider("長期均線（天）", min_value=20, max_value=200, value=60)
    run_btn = st.button("🚀 開始分析", use_container_width=True)

# ─── 主程式 ─────────────────────────────────────────────────────────────────
if run_btn:
    if short_window >= long_window:
        st.error("❌ 短期均線天數必須小於長期均線天數！")
        st.stop()

    with st.spinner(f"正在下載 {ticker} 資料..."):
        try:
            df = yf.download(ticker, start=str(start_date), end=str(end_date), auto_adjust=True)
        except Exception as e:
            st.error(f"下載失敗：{e}")
            st.stop()

    if df.empty:
        st.error("❌ 找不到該股票資料，請確認股票代號是否正確。")
        st.stop()

    # 壓平多層欄位（yfinance 新版會產生 MultiIndex）
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 計算 SMA
    df['SMA_Short'] = df['Close'].rolling(window=short_window).mean()
    df['SMA_Long']  = df['Close'].rolling(window=long_window).mean()

    # 計算訊號
    df['Signal'] = 0
    df.iloc[short_window:, df.columns.get_loc('Signal')] = (
        (df['SMA_Short'][short_window:] > df['SMA_Long'][short_window:]).astype(int)
    )
    df['Position'] = df['Signal'].diff()

    buy_signals  = df[df['Position'] == 1]
    sell_signals = df[df['Position'] == -1]

    # ─── 關鍵數據卡 ──────────────────────────────────────────────────────────
    latest_close = float(df['Close'].iloc[-1])
    total_return = (df['Close'].iloc[-1] / df['Close'].iloc[0] - 1) * 100
    num_buys  = len(buy_signals)
    num_sells = len(sell_signals)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("最新收盤價", f"${latest_close:.2f}")
    c2.metric("期間報酬率", f"{float(total_return):.1f}%")
    c3.metric("🟢 買進訊號次數", num_buys)
    c4.metric("🔴 賣出訊號次數", num_sells)

    # ─── 圖表 ────────────────────────────────────────────────────────────────
    st.subheader("📊 價格與均線走勢")
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')

    ax.plot(df.index, df['Close'],     color='#a0c4ff', linewidth=1.2,  label='收盤價',            alpha=0.8)
    ax.plot(df.index, df['SMA_Short'], color='#f9c74f', linewidth=1.5,  label=f'{short_window}日均線')
    ax.plot(df.index, df['SMA_Long'],  color='#f94144', linewidth=1.5,  label=f'{long_window}日均線')

    ax.scatter(buy_signals.index,  buy_signals['Close'],  marker='^', color='#90be6d', s=80, zorder=5, label='買進訊號 ▲')
    ax.scatter(sell_signals.index, sell_signals['Close'], marker='v', color='#f9c74f', s=80, zorder=5, label='賣出訊號 ▼')

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45, color='white')
    plt.yticks(color='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333')
    ax.grid(color='#333', linestyle='--', linewidth=0.5, alpha=0.7)
    ax.legend(facecolor='#1a1a2e', edgecolor='#444', labelcolor='white')
    ax.set_title(f"{ticker} SMA 均線交叉策略", color='white', fontsize=14)
    plt.tight_layout()
    st.pyplot(fig)

    # ─── 最近10筆資料表 ───────────────────────────────────────────────────────
    st.subheader("📋 最近 10 筆數據")
    show_cols = ['Close', 'SMA_Short', 'SMA_Long', 'Signal', 'Position']
    st.dataframe(
        df[show_cols].tail(10).round(2),
        use_container_width=True
    )

else:
    st.info("👈 請在左側設定參數後，點擊「開始分析」按鈕")
    st.markdown("""
    ### 📖 使用說明
    1. 在左側輸入**股票代號**（如 `TSM`、`AAPL`、`0050.TW`）
    2. 選擇**分析日期範圍**
    3. 調整**短期**與**長期均線**天數
    4. 點擊「🚀 開始分析」查看結果

    ### 📌 策略說明
    - **黃金交叉 ▲**：短期均線從下方穿越長期均線 → 買進訊號
    - **死亡交叉 ▼**：短期均線從上方跌破長期均線 → 賣出訊號
    """)
