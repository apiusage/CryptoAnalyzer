import streamlit as st
import requests
import pandas as pd
import yfinance as yf
from bs4 import BeautifulSoup
import numpy as np
import warnings

def get_technicals_stats(coin_symbol):
    technicals_url = (
        f"https://www.tradingview.com/symbols/{coin_symbol}/technicals/"
    )
    st.markdown(f'[View Tradingview Technicals for {coin_symbol}]({technicals_url})')

# https://cointelegraph.com/news/john-bollinger-says-to-pay-attention-soon-as-big-move-could-be-imminent
def btc_weekly_dashboard_complete():
    # Fetch BTC weekly data
    df = yf.download("BTC-USD", period="5y", interval="1wk", auto_adjust=True)

    # Latest price
    price = float(df['Close'].iloc[-1].item())

    # ---
    # 1️⃣ Moving Averages
    sma50 = float(df['Close'].rolling(50).mean().iloc[-1].item())
    sma200 = float(df['Close'].rolling(200).mean().iloc[-1].item())
    pct_diff = (sma50 - sma200) / sma200 * 100
    threshold = 2

    st.markdown("**📈 Trend:** " + (
        "⚠️ Near Death Cross (bearish warning)" if sma50 < sma200 and abs(pct_diff) <= threshold else
        "💀 Death Cross — trend is bearish" if sma50 < sma200 else
        "⚠️ Near Golden Cross (bullish warning)" if abs(pct_diff) <= threshold else
        "🌟 Golden Cross — trend is bullish"
    ))

    st.markdown("**🟡 50-week SMA:** " +
                ("Near price — buying zone" if price <= sma50 * 1.01 else "Above price — trend healthy"))
    st.markdown("**🟠 200-week SMA:** " +
                ("Near price — strong support" if price <= sma200 * 1.05 else "Above price — long-term bullish"))

    # ---
    # 2️⃣ Bollinger Bands (volatility)
    ma20 = df['Close'].rolling(20).mean().iloc[-1].item()
    std20 = df['Close'].rolling(20).std().iloc[-1].item()
    bandwidth = float((ma20 + 2*std20 - (ma20 - 2*std20)) / ma20 * 100)

    st.markdown("**⚡ Volatility:** " + (
        "Low — market quiet" if bandwidth < 10 else f"Normal ({bandwidth:.2f}%)"
    ))

    # ---
    # 3️⃣ ATR (14-week)
    high, low, close = df['High'], df['Low'], df['Close']
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1].item())
    st.markdown("**📏 ATR:** " + (
        "High — very volatile" if atr > price*0.05 else
        "Low — quiet market" if atr < price*0.02 else
        "Moderate — normal weekly moves"
    ))

    # ---
    # 4️⃣ RSI (14-week)
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = float(gain.rolling(14).mean().iloc[-1].item())
    avg_loss = float(loss.rolling(14).mean().iloc[-1].item())
    rs = avg_gain / avg_loss if avg_loss != 0 else 100
    rsi = 100 - (100 / (1 + rs))
    rsi_val = float(rsi)

    st.markdown("**📊 RSI:** " + (
        "Overbought — possible pullback" if rsi_val > 70 else
        "Oversold — possible rebound" if rsi_val < 30 else
        "Normal"
    ))

    # ---
    # 5️⃣ Weekly Volume
    latest_vol = float(df['Volume'].iloc[-1].item())
    avg_vol50 = float(df['Volume'].rolling(50).mean().iloc[-1].item())
    st.markdown("**📈 Volume:** " + (
        "High — strong market activity" if latest_vol > avg_vol50 * 1.5 else
        "Low — weak activity" if latest_vol < avg_vol50 * 0.7 else
        "Normal — market stable"
    ))

    # ---
    # 6️⃣ Big Movement Warning
    big_move = False
    if bandwidth < 10 and atr > price*0.03 and latest_vol > avg_vol50 * 1.2:
        big_move = True

    # MACD values
    macd_short = df['Close'].ewm(span=12).mean()
    macd_long = df['Close'].ewm(span=26).mean()
    macd = macd_short - macd_long
    signal = macd.ewm(span=9).mean()
    macd_val = float(macd.iloc[-1].item())
    signal_val = float(signal.iloc[-1].item())

    if macd_val > signal_val and price > sma50:
        direction = "bullish 📈"
    elif macd_val < signal_val and price < sma50:
        direction = "bearish 📉"
    else:
        direction = "uncertain ⚖️"

    if big_move:
        st.markdown(f"**⚠️ Big Movement Likely:** All indicators suggest upcoming volatility, likely {direction}!")
    else:
        st.markdown("**ℹ️ No big movement expected soon**")

    # ---
    # 7️⃣ Enhanced Momentum + Volume Detector (RSI + MACD + MFI)
    # Money Flow Index (MFI)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    pos_flow = money_flow.where(typical_price > typical_price.shift(1), 0.0)
    neg_flow = money_flow.where(typical_price < typical_price.shift(1), 0.0)

    pos_sum = float(pos_flow.rolling(14).sum().iloc[-1].item())
    neg_sum = float(neg_flow.rolling(14).sum().iloc[-1].item())
    mfr = pos_sum / neg_sum if neg_sum != 0 else 0
    mfi = 100 - (100 / (1 + mfr))
    mfi_val = float(mfi)

    # Weighted detector
    rsi_weight = 0.4
    macd_weight = 0.4
    mfi_weight = 0.2

    # Normalize scores
    rsi_score = rsi_val / 100

    # --- Use stable sigmoid to prevent overflow
    def stable_sigmoid(x):
        x = np.clip(x, -50, 50)
        return 1 / (1 + np.exp(-x))

    macd_score = stable_sigmoid(macd_val - signal_val)
    mfi_score = mfi_val / 100

    momentum_score = rsi_score*rsi_weight + macd_score*macd_weight + mfi_score*mfi_weight

    bullish_threshold = 0.6
    bearish_threshold = 0.4

    if momentum_score >= bullish_threshold:
        st.markdown("**🚀 Enhanced Detector:** Bullish — momentum and volume strongly confirm upside.")
    elif momentum_score <= bearish_threshold:
        st.markdown("**⚰️ Enhanced Detector:** Bearish — downside pressure is significant.")
    else:
        st.markdown("**⚖️ Enhanced Detector:** Neutral — mixed momentum, unclear volume trends.")

def display_unified_confidence_score(df, price=None):
    """
    Calculate and display a unified BTC confidence score (0-100%) in Streamlit.

    Parameters:
    - df: pandas DataFrame containing 'Close', 'High', 'Low', 'Volume'
    - price: optional, latest BTC price (will take last Close if None)
    """
    if price is None:
        price = float(df['Close'].iloc[-1].item())

    # --- Trend score
    sma50 = df['Close'].rolling(50).mean().iloc[-1].item()
    sma200 = df['Close'].rolling(200).mean().iloc[-1].item()
    trend_score = np.clip((sma50 - sma200)/sma200 + 0.5, 0, 1)

    # --- Momentum score (RSI + MACD)
    close = df['Close']
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean().iloc[-1].item()
    avg_loss = loss.rolling(14).mean().iloc[-1].item()
    rs = avg_gain / avg_loss if avg_loss !=0 else 100
    rsi_val = 100 - (100 / (1 + rs))
    rsi_score = rsi_val / 100

    macd_short = df['Close'].ewm(span=12).mean()
    macd_long = df['Close'].ewm(span=26).mean()
    macd = macd_short - macd_long
    signal = macd.ewm(span=9).mean()
    macd_val = macd.iloc[-1].item()
    signal_val = signal.iloc[-1].item()

    # --- Stable sigmoid for MACD
    def stable_sigmoid(x):
        x = np.clip(x, -50, 50)  # prevent overflow
        return 1 / (1 + np.exp(-x))

    macd_score = stable_sigmoid(macd_val - signal_val)
    momentum_score = 0.5 * rsi_score + 0.5 * macd_score

    # --- Volume score (MFI)
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    money_flow = typical_price * df['Volume']
    pos_flow = money_flow.where(typical_price > typical_price.shift(1), 0.0)
    neg_flow = money_flow.where(typical_price < typical_price.shift(1), 0.0)
    pos_sum = pos_flow.rolling(14).sum().iloc[-1].item()
    neg_sum = neg_flow.rolling(14).sum().iloc[-1].item()
    mfi_val = 100 - (100 / (1 + (pos_sum / neg_sum if neg_sum != 0 else 0)))
    volume_score = mfi_val / 100

    # --- Volatility score (ATR normalized)
    high, low = df['High'], df['Low']
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1].item()
    volatility_score = np.clip(atr / price * 20, 0, 1)

    # --- Weighted final score
    final_score = 0.2*trend_score + 0.4*momentum_score + 0.2*volume_score + 0.2*volatility_score
    final_score_pct = final_score * 100

    # --- Display nicely in Streamlit
    st.markdown("### 📌 Unified Market Confidence Score")
    st.progress(final_score)
    if final_score >= 0.7:
        st.success(f"Strongly Bullish — Confidence: {final_score_pct:.1f}%")
    elif final_score >= 0.55:
        st.info(f"Bullish — Confidence: {final_score_pct:.1f}%")
    elif final_score >= 0.45:
        st.warning(f"Neutral / Sideways — Confidence: {final_score_pct:.1f}%")
    elif final_score >= 0.3:
        st.info(f"Bearish — Confidence: {final_score_pct:.1f}%")
    else:
        st.error(f"Strongly Bearish — Confidence: {final_score_pct:.1f}%")

    # Return values for further use if needed
    return {
        "final_score": final_score,
        "trend_score": trend_score,
        "momentum_score": momentum_score,
        "volume_score": volume_score,
        "volatility_score": volatility_score,
        "rsi_val": rsi_val,
        "macd_val": macd_val,
        "mfi_val": mfi_val,
        "atr": atr
    }

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

def live_market_ticker():
    """Ultra-condensed, actionable market ticker for pro traders (stocks, FX, yields, commodities, yields)."""
    import warnings
    import yfinance as yf
    import pandas as pd
    import streamlit as st

    # --- Helpers ---
    def get_yahoo_change_safe(symbol):
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = yf.download(symbol, period="2d", interval="1d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 2:
                return 0.0
            last = float(df["Close"].iat[-1])
            prev = float(df["Close"].iat[-2])
            return (last - prev) / prev * 100
        except:
            return 0.0

    # --- Fetch data ---
    dxy = get_yahoo_change_safe("DX-Y.NYB")
    vix = get_yahoo_change_safe("^VIX")
    spx = get_yahoo_change_safe("^GSPC")
    qqq = get_yahoo_change_safe("QQQ")
    dow = get_yahoo_change_safe("^DJI")
    gold = get_yahoo_change_safe("GC=F")
    silver = get_yahoo_change_safe("SI=F")
    oil = get_yahoo_change_safe("CL=F")
    tnx = get_yahoo_change_safe("^TNX")
    t2y = get_yahoo_change_safe("^IRX")
    eurusd = get_yahoo_change_safe("EURUSD=X")
    jpyusd = get_yahoo_change_safe("JPY=X")

    # --- Build actionable insights ---
    actions = []

    # Equities
    if spx < -0.3 or qqq < -0.3:
        actions.append("📉 Stocks down → cautious")
    elif spx > 0.3 or qqq > 0.3:
        actions.append("📈 Stocks up → consider buying")
    else:
        actions.append("🟡 Stocks stable → holding pattern")

    if dow < -0.3:
        actions.append("📉 Dow down → risk-off")
    elif dow > 0.3:
        actions.append("📈 Dow up → industrials strong")

    # USD / FX
    if dxy > 0.2:
        actions.append("💵 USD strong → exporters pressured")
    elif dxy < -0.2:
        actions.append("💵 USD weak → exporters benefit")
    else:
        actions.append("🟢 USD steady → balanced FX")

    if eurusd < -0.2:
        actions.append("🇪🇺 EUR down → USD strength")
    elif eurusd > 0.2:
        actions.append("🇪🇺 EUR up → USD weakness")

    if jpyusd < -0.2:
        actions.append("🇯🇵 JPY down → USD strength")
    elif jpyusd > 0.2:
        actions.append("🇯🇵 JPY up → yen strengthening")

    # Volatility
    if vix > 2:
        actions.append("⚠️ VIX high → cautious")
    elif vix < -2:
        actions.append("✅ VIX low → market calm")
    else:
        actions.append("ℹ️ VIX neutral → normal volatility")

    # Commodities
    if gold > 0.3:
        actions.append("🥇 Gold up → safe-haven strong")
    elif gold < -0.3:
        actions.append("🥇 Gold down → consider selling")
    else:
        actions.append("🟡 Gold stable → holding value")

    if silver > 0.3:
        actions.append("🥈 Silver up → industrial/hedge strong")
    elif silver < -0.3:
        actions.append("🥈 Silver down → weak")

    if oil > 0.3:
        actions.append("🛢 Oil up → energy strong")
    elif oil < -0.3:
        actions.append("🛢 Oil down → energy weak")
    else:
        actions.append("🟢 Oil stable → energy balanced")

    # Yields
    if tnx > 0.2:
        actions.append("📊 10Y yields rising → bonds less attractive")
    elif tnx < -0.2:
        actions.append("📊 10Y yields down → bonds attractive")
    else:
        actions.append("ℹ️ 10Y yields flat → rates steady")

    if t2y > 0.2:
        actions.append("📈 2Y rising → short-term rates higher")
    elif t2y < -0.2:
        actions.append("📉 2Y down → short-term rates lower")
    else:
        actions.append("ℹ️ 2Y flat → short rates stable")

    # ------------------ Combine text ------------------
    brief_text = " | ".join(actions) if actions else "Market steady, no major moves."

    # ------------------ Horizontal scrolling ticker ------------------
    ticker_html = f"""
    <div style='overflow:hidden; white-space:nowrap; background-color:#000; padding:10px 0; border-radius:10px;'>
        <div style='display:inline-block; padding-left:100%;
                    animation: ticker 60s linear infinite;
                    font-size:20px; font-weight:600; color:#00ffcc;
                    font-family:"Segoe UI", Arial, sans-serif;'>
            💡 {brief_text} &nbsp;&nbsp;&nbsp; 💡 {brief_text}
        </div>
    </div>
    <style>
    @keyframes ticker {{
        0% {{ transform: translateX(0%); }}
        100% {{ transform: translateX(-100%); }}
    }}
    </style>
    """
    st.markdown(ticker_html, unsafe_allow_html=True)

