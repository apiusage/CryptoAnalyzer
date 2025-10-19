import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup

def get_technicals_stats(coin_symbol):
    technicals_url = (
        f"https://www.tradingview.com/symbols/{coin_symbol}/technicals/"
    )
    st.markdown(f'[View Tradingview Technicals for {coin_symbol}]({technicals_url})')

# https://cointelegraph.com/news/john-bollinger-says-to-pay-attention-soon-as-big-move-could-be-imminent
def btc_weekly_dashboard_complete():
    # Fetch BTC weekly data
    df = yf.download("BTC-USD", period="5y", interval="1wk")

    # Latest price
    price = float(df['Close'].iloc[-1])
    # st.markdown(f"**💰 Current Price:** ${price:,.0f}")

    # --- 1️⃣ Moving Averages ---
    sma50 = float(df['Close'].rolling(50).mean().iloc[-1])
    sma200 = float(df['Close'].rolling(200).mean().iloc[-1])
    pct_diff = (sma50 - sma200) / sma200 * 100
    threshold = 2

    # Death / Golden Cross
    st.markdown("**📈 Trend:** " +
                ("⚠️ Near Death Cross (bearish warning)" if sma50 < sma200 and abs(pct_diff) <= threshold else
                 "💀 Death Cross — trend is bearish" if sma50 < sma200 else
                 "⚠️ Near Golden Cross (bullish warning)" if abs(pct_diff) <= threshold else
                 "🌟 Golden Cross — trend is bullish"))

    # 50-week SMA
    st.markdown("**🟡 50-week SMA:** " +
                ("Near price — buying zone" if price <= sma50 * 1.01 else "Above price — trend healthy"))

    # 200-week SMA
    st.markdown("**🟠 200-week SMA:** " +
                ("Near price — strong support" if price <= sma200 * 1.05 else "Above price — long-term bullish"))

    # --- 2️⃣ Bollinger Bands (volatility) ---
    ma20 = df['Close'].rolling(20).mean().iloc[-1]
    std20 = df['Close'].rolling(20).std().iloc[-1]
    bandwidth = float((ma20 + 2*std20 - (ma20 - 2*std20)) / ma20 * 100)
    st.markdown("**⚡ Volatility:** " +
                ("Low — market quiet" if bandwidth < 10 else f"Normal ({bandwidth:.2f}%)"))

    # --- 3️⃣ ATR (14-week) ---
    high = df['High']
    low = df['Low']
    close = df['Close']
    tr = pd.concat([high - low,
                    (high - close.shift(1)).abs(),
                    (low - close.shift(1)).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])
    st.markdown("**📏 ATR:** " +
                ("High — very volatile" if atr > price*0.05 else
                 "Low — quiet market" if atr < price*0.02 else
                 "Moderate — normal weekly moves"))

    # --- 4️⃣ RSI (14-week) ---
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = float(gain.rolling(14).mean().iloc[-1])
    avg_loss = float(loss.rolling(14).mean().iloc[-1])
    rs = avg_gain / avg_loss if avg_loss != 0 else 100
    rsi = 100 - (100 / (1 + rs))
    st.markdown("**📊 RSI:** " +
                ("Overbought — possible pullback" if rsi > 70 else
                 "Oversold — possible rebound" if rsi < 30 else
                 "Normal"))

    # --- 5️⃣ Weekly Volume ---
    latest_vol = float(df['Volume'].iloc[-1])
    avg_vol50 = float(df['Volume'].rolling(50).mean().iloc[-1])
    st.markdown("**📈 Volume:** " +
                ("High — strong market activity" if latest_vol > avg_vol50 * 1.5 else
                 "Low — weak activity" if latest_vol < avg_vol50 * 0.7 else
                 "Normal — market stable"))

    # --- 6️⃣ Big Movement Warning ---
    # Combine ATR, Bollinger, and Volume
    big_move = False
    if bandwidth < 10 and atr > price*0.03 and latest_vol > avg_vol50 * 1.2:
        big_move = True
        # Determine likely direction
        macd_short = df['Close'].ewm(span=12).mean()
        macd_long = df['Close'].ewm(span=26).mean()
        macd = macd_short - macd_long
        signal = macd.ewm(span=9).mean()

        if macd.iloc[-1] > signal.iloc[-1] and price > sma50:
            direction = "bullish 📈"
        elif macd.iloc[-1] < signal.iloc[-1] and price < sma50:
            direction = "bearish 📉"
        else:
            direction = "uncertain ⚖️"

    if big_move:
        st.markdown(f"**⚠️ Big Movement Likely:** All indicators suggest upcoming volatility, likely {direction}!")
    else:
        st.markdown("**ℹ️ No big movement expected soon**")

def get_coinbase_app_rank():
    """Fetch Coinbase App Store rank and display in Streamlit."""
    url = "https://apps.apple.com/us/app/coinbase-buy-bitcoin-ether/id886427730"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    rank_tag = soup.find("a", {"class": "inline-list__item"})
    if rank_tag:
        rank = rank_tag.get_text(strip=True)
        st.write(f"**📱 Coinbase App Store Rank:** {rank}")
    else:
        st.write("**📱 Coinbase App Store Rank:** Not found")