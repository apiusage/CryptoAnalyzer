import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
import numpy as np
import warnings

def get_technicals_stats(coin_symbol):
    url = f"https://www.tradingview.com/symbols/{coin_symbol}/technicals/"
    st.markdown(f'[View Tradingview Technicals for {coin_symbol}]({url})')

def btc_weekly_dashboard_complete():
    df = yf.download("BTC-USD", period="5y", interval="1wk", auto_adjust=True)
    if df.empty or 'Close' not in df.columns:
        st.error("Error fetching BTC data")
        return

    close = df['Close'].squeeze() if isinstance(df['Close'], pd.DataFrame) else df['Close']
    close = pd.to_numeric(close, errors='coerce')
    price = close.iloc[-1].item()

    # SMAs
    smas = {name: close.rolling(p).mean().iloc[-1].item()
            for name, p in [("SMA9", 9), ("SMA20", 20), ("SMA50", 50), ("SMA200", 200)]}

    # Death/Golden Cross
    pct_diff = (smas['SMA50'] - smas['SMA200']) / smas['SMA200'] * 100
    if smas['SMA50'] < smas['SMA200']:
        trend = "⚠️ Near Death Cross" if abs(pct_diff) <= 2 else "💀 Death Cross"
    else:
        trend = "⚠️ Near Golden Cross" if abs(pct_diff) <= 2 else "🌟 Golden Cross"
    st.markdown(f"**📈 Trend:** {trend}")

    # Bollinger Bandwidth
    ma20 = close.rolling(20).mean().iloc[-1].item()
    std20 = close.rolling(20).std().iloc[-1].item()
    bandwidth = 4 * std20 / ma20 * 100
    st.markdown(f"**⚡ Volatility:** {'Low — quiet' if bandwidth < 10 else f'Normal ({bandwidth:.1f}%)'}")

    # ATR
    tr = pd.concat([df['High'] - df['Low'],
                    (df['High'] - close.shift()).abs(),
                    (df['Low'] - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1].item()
    atr_msg = ("High — volatile" if atr > price * 0.05 else
               "Low — quiet" if atr < price * 0.02 else "Moderate")
    st.markdown(f"**📏 ATR:** {atr_msg}")

    # RSI
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean().iloc[-1].item()
    loss = -delta.clip(upper=0).rolling(14).mean().iloc[-1].item()
    rsi = 100 - 100 / (1 + gain / loss) if loss else 100
    rsi_msg = ("Overbought" if rsi > 70 else "Oversold" if rsi < 30 else "Normal")
    st.markdown(f"**📊 RSI:** {rsi_msg}")

    # Volume
    vol = df['Volume'].iloc[-1].item()
    avg_vol = df['Volume'].rolling(50).mean().iloc[-1].item()
    vol_msg = ("High — strong" if vol > avg_vol * 1.5 else
               "Low — weak" if vol < avg_vol * 0.7 else "Normal")
    st.markdown(f"**📈 Volume:** {vol_msg}")

    # MACD
    macd = close.ewm(span=12).mean() - close.ewm(span=26).mean()
    signal = macd.ewm(span=9).mean()
    macd_val, sig_val = macd.iloc[-1].item(), signal.iloc[-1].item()

    direction = ("bullish 📈" if macd_val > sig_val and price > smas['SMA50'] else
                 "bearish 📉" if macd_val < sig_val and price < smas['SMA50'] else
                 "uncertain ⚖️")

    # Big Move Warning
    big_move = bandwidth < 10 and atr > price * 0.03 and vol > avg_vol * 1.2
    st.markdown(f"**{'⚠️ Big Movement Likely' if big_move else 'ℹ️ No big movement'}:** "
                f"{'Indicators suggest volatility, likely ' + direction if big_move else 'expected soon'}")

    # Enhanced Momentum (MFI)
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    mf = tp * df['Volume']
    pos = mf.where(tp > tp.shift(), 0).rolling(14).sum().iloc[-1].item()
    neg = mf.where(tp < tp.shift(), 0).rolling(14).sum().iloc[-1].item()
    mfi = 100 - 100 / (1 + pos / neg) if neg else 100

    # Momentum Score
    rsi_s = rsi / 100
    macd_s = 1 / (1 + np.exp(-np.clip(macd_val - sig_val, -50, 50)))
    mfi_s = mfi / 100
    score = 0.4 * rsi_s + 0.4 * macd_s + 0.2 * mfi_s

    st.markdown(f"**{'🚀' if score >= 0.6 else '⚰️' if score <= 0.4 else '⚖️'} Enhanced Detector:** "
                f"{'Bullish — strong upside' if score >= 0.6 else 'Bearish — downside pressure' if score <= 0.4 else 'Neutral — mixed signals'}")

def sma_signal_table():
    df = yf.download("BTC-USD", period="5y", interval="1wk", auto_adjust=True)
    if df.empty:
        st.error("Error fetching BTC data")
        return

    close = df['Close'].squeeze() if isinstance(df['Close'], pd.DataFrame) else df['Close']
    price = close.iloc[-1].item()

    st.markdown(f"**💰 Current Price:** ${price:,.2f}")
    st.markdown("Price > SMA → BUY (bullish) | Price < SMA → SELL (bearish)")

    def timeframe(weeks):
        if weeks < 4:
            return f"~{weeks * 7} days"
        elif weeks < 52:
            return f"{round(weeks / 4.5)}-{round(weeks / 4)} months"
        else:
            return f"~{round(weeks / 52, 1)} years"

    sma_data = [
        ("SMA9", "🔹", 9),
        ("SMA20", "🔸", 20),
        ("SMA50", "🟡", 50),
        ("SMA200", "🟠", 200)
    ]

    table = []
    for name, emoji, weeks in sma_data:
        sma = close.rolling(weeks).mean().iloc[-1].item()
        signal = "BUY" if price > sma else "SELL"
        table.append({
            "Signal": signal,
            "SMA": f"{emoji} {name}",
            "SMA Value": round(sma, 2),
            "Timeframe": timeframe(weeks)
        })

    df_table = pd.DataFrame(table)
    st.dataframe(df_table.style.map(
        lambda
            v: "color: green; font-weight: bold" if v == "BUY" else "color: red; font-weight: bold" if v == "SELL" else "",
        subset=["Signal"]
    ))

def display_unified_confidence_score(df, price=None):
    if price is None:
        price = df['Close'].iloc[-1].item()

    close = df['Close'].squeeze() if isinstance(df['Close'], pd.DataFrame) else df['Close']
    close = pd.to_numeric(close, errors='coerce')

    # Trend
    sma50 = close.rolling(50).mean().iloc[-1].item()
    sma200 = close.rolling(200).mean().iloc[-1].item()
    trend_s = np.clip((sma50 - sma200) / sma200 + 0.5, 0, 1)

    # Momentum (RSI + MACD)
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean().iloc[-1].item()
    loss = -delta.clip(upper=0).rolling(14).mean().iloc[-1].item()
    rsi = 100 - 100 / (1 + gain / loss) if loss else 100

    macd = close.ewm(span=12).mean() - close.ewm(span=26).mean()
    signal = macd.ewm(span=9).mean()
    macd_s = 1 / (1 + np.exp(-np.clip((macd.iloc[-1] - signal.iloc[-1]).item(), -50, 50)))
    momentum_s = 0.5 * rsi / 100 + 0.5 * macd_s

    # Volume (MFI)
    tp = (df['High'] + df['Low'] + df['Close']) / 3
    mf = tp * df['Volume']
    pos = mf.where(tp > tp.shift(), 0).rolling(14).sum().iloc[-1].item()
    neg = mf.where(tp < tp.shift(), 0).rolling(14).sum().iloc[-1].item()
    mfi = 100 - 100 / (1 + pos / neg) if neg else 100
    volume_s = mfi / 100

    # Volatility (ATR)
    tr = pd.concat([df['High'] - df['Low'],
                    (df['High'] - close.shift()).abs(),
                    (df['Low'] - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1].item()
    volatility_s = np.clip(atr / price * 20, 0, 1)

    # Final Score
    score = 0.2 * trend_s + 0.4 * momentum_s + 0.2 * volume_s + 0.2 * volatility_s
    pct = score * 100

    st.markdown("### 📌 Unified Market Confidence Score")
    st.progress(score)

    if score >= 0.7:
        st.success(f"Strongly Bullish — {pct:.1f}%")
    elif score >= 0.55:
        st.info(f"Bullish — {pct:.1f}%")
    elif score >= 0.45:
        st.warning(f"Neutral — {pct:.1f}%")
    elif score >= 0.3:
        st.info(f"Bearish — {pct:.1f}%")
    else:
        st.error(f"Strongly Bearish — {pct:.1f}%")

    return {"score": score, "trend": trend_s, "momentum": momentum_s,
            "volume": volume_s, "volatility": volatility_s, "rsi": rsi,
            "macd": macd.iloc[-1].item(), "mfi": mfi, "atr": atr}

def get_coinbase_app_rank():
    try:
        r = requests.get("https://apps.apple.com/us/app/coinbase-buy-bitcoin-ether/id886427730",
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        rank = soup.find("a", {"class": "inline-list__item"})
        st.write(f"**📱 Coinbase Rank:** {rank.get_text(strip=True) if rank else 'Not found'}")
    except:
        st.write("**📱 Coinbase Rank:** Error fetching")

def live_market_ticker():
    def get_chg(sym):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = yf.download(sym, period="2d", interval="1d", progress=False, auto_adjust=True)
            if len(df) < 2:
                return 0.0
            return (df["Close"].iat[-1] - df["Close"].iat[-2]) / df["Close"].iat[-2] * 100
        except:
            return 0.0

    # Fetch all at once
    syms = ["^GSPC", "QQQ", "^DJI", "DX-Y.NYB", "^VIX", "GC=F", "SI=F",
            "CL=F", "^TNX", "^IRX", "EURUSD=X", "JPY=X"]
    spx, qqq, dow, dxy, vix, gold, silver, oil, tnx, t2y, eur, jpy = [get_chg(s) for s in syms]

    actions = []

    # Equities
    if spx < -0.3 or qqq < -0.3:
        actions.append("📉 Stocks down")
    elif spx > 0.3 or qqq > 0.3:
        actions.append("📈 Stocks up")
    else:
        actions.append("🟡 Stocks flat")

    # USD
    if dxy > 0.2:
        actions.append("💵 USD strong")
    elif dxy < -0.2:
        actions.append("💵 USD weak")
    else:
        actions.append("💵 USD neutral")

    # Volatility
    if vix > 2:
        actions.append("⚠️ VIX high")
    elif vix < -2:
        actions.append("✅ VIX low")
    else:
        actions.append("⚪ VIX stable")

    # Commodities
    if gold > 0.3:
        actions.append("🥇 Gold up")
    elif gold < -0.3:
        actions.append("🥇 Gold down")

    if oil > 0.3:
        actions.append("🛢 Oil up")
    elif oil < -0.3:
        actions.append("🛢 Oil down")

    # Yields
    if tnx > 0.2:
        actions.append("📊 10Y rising")
    elif tnx < -0.2:
        actions.append("📊 10Y falling")

    brief = " | ".join(actions) if actions else "Market stable"

    ticker_html = f"""
    <div style='overflow:hidden; white-space:nowrap; background:#000; padding:10px 0; border-radius:10px;'>
        <div style='display:inline-block; padding-left:100%; animation: ticker 60s linear infinite;
                    font-size:20px; font-weight:600; color:#00ffcc; font-family:Arial,sans-serif;'>
            💡 {brief} &nbsp;&nbsp;&nbsp; 💡 {brief}
        </div>
    </div>
    <style>@keyframes ticker {{0%{{transform:translateX(0)}}100%{{transform:translateX(-100%)}}}}</style>
    """
    st.markdown(ticker_html, unsafe_allow_html=True)
