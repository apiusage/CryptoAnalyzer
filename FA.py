import streamlit as st
import requests
import urllib.parse
import pandas as pd
from datetime import datetime
from st_copy_to_clipboard import st_copy_to_clipboard

CMC_API_KEY = 'fcf7ee51-af70-4614-821a-f253d1f0d7da'

def gpt_prompt_copy(txt_file, placeholder="", replacement="", name="", key_suffix="", show_text=False):
    try:
        content = open(txt_file, encoding="utf-8").read().replace(placeholder, replacement)
        st_copy_to_clipboard(content,
                             before_copy_label=f"📋 {name}" if name else "Copy Prompt",
                             after_copy_label="✅ Text copied!",
                             show_text=show_text,
                             key=f"copy_{hash(replacement)}_{key_suffix}")
    except Exception as e:
        st.error(f"Error: {e}")


def gpt_prompt_copy_msg(prefix, suffix, coin_list):
    st_copy_to_clipboard(f"{prefix}{coin_list}{suffix}",
                         before_copy_label="Copy Prompt",
                         after_copy_label="✅ Text copied!")

@st.cache_data(show_spinner=False)
def get_coin_data():
    return requests.get("https://api.coingecko.com/api/v3/coins/markets", params={
        'vs_currency': 'usd', 'order': 'market_cap_desc',
        'per_page': 200, 'page': 1, 'sparkline': 'false'
    })

@st.cache_data(show_spinner=False)
def get_coin_categories():
    categories = requests.get("https://api.coingecko.com/api/v3/coins/categories").json()
    coin_to_cat = {}
    for cat in categories:
        for coin_id in cat.get("top_3_coins_id", []):
            coin_to_cat.setdefault(coin_id, []).append(cat.get("name"))
    return coin_to_cat

def get_coin_creation_date(coin_id):
    """Fetch and display the creation (genesis) date of a cryptocurrency from CoinGecko."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    r = requests.get(url)

    if r.status_code == 200:
        date = r.json().get('genesis_date', None)
        if date:
            st.metric("Creation Date", date, border=True)
        else:
            st.warning("⚠️ Creation date not provided by CoinGecko.")
    else:
        # --- Friendly error messages ---
        if r.status_code == 404:
            st.error("❌ Coin not found (invalid coin ID).")
        elif r.status_code == 429:
            st.error("⏳ Too many requests — please wait a bit and try again.")
        elif r.status_code >= 500:
            st.error("⚠️ CoinGecko server error. Try again later.")
        else:
            st.error(f"⚠️ Unexpected error (HTTP {r.status_code}).")

# --- Helper: label + emoji for index value ---
def fng_label(value: int):
    if value <= 24:
        return "😱 Extreme Fear"
    elif value <= 49:
        return "😟 Fear"
    elif value <= 74:
        return "🙂 Greed"
    else:
        return "🤯 Extreme Greed"

# --- Fetch Function ---
def fetch_fng(api_source):
    def process(data):
        timestamps = [int(e['timestamp']) for e in data]
        values = [int(float(e['value'])) for e in data]
        dates = [datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps]
        return pd.DataFrame({'Date': pd.to_datetime(dates), 'Fear and Greed Index': values})

    if api_source == "alternative_me":
        data = requests.get("https://api.alternative.me/fng/?limit=20").json()['data']
        return process(data)

    elif api_source == "coinmarketcap":
        r = requests.get(
            "https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical",
            headers={'X-CMC_PRO_API_KEY': CMC_API_KEY, 'Accept': 'application/json'},
            params={'limit': 30, 'convert': 'USD'}
        )
        if r.status_code == 200:
            return process(r.json()['data'])
        else:
            st.error(f"Error: {r.status_code}")
            return pd.DataFrame()
    else:
        st.error("Invalid API source")
        return pd.DataFrame()

def get_google_trends(coin_name, language="en"):
    url = f"https://trends.google.com/trends/explore?&q={urllib.parse.quote(coin_name)}&hl={language}"
    st.markdown(f'[View Google Trends for {coin_name}]({url})')

def classify_market_cap(mcap):
    msg = ("Nano Cap - < $1M" if mcap < 1_000_000 else
           "Micro Cap - $1M-$10M" if mcap < 10_000_000 else
           "Small Cap - $10M-$100M" if mcap < 100_000_000 else
           "Large Cap - > $100M")
    st.success(msg)

def calculate_vol_mcap_ratio(mcap, vol):
    ratio = vol / mcap if mcap else 0
    st.success("Liquidity and trading activity - >30% = Buy")
    st.metric("Vol. (24h) / MCap Ratio", f"{ratio:.4f}", delta=f"{ratio * 100:.2f}%", border=True)

    if ratio > 0.1:
        st.markdown("- **High Ratio** (>10%): Active trading, high liquidity\n- Popular or experiencing surge")
    elif ratio > 0.01:
        st.markdown("- **Moderate Ratio** (>1%): Moderate liquidity, stable coin")
    else:
        st.markdown("- **Low Ratio**: Limited trading, low liquidity\n- Risk of price slippage")

def check_increased_trading_volume(coin_symbol):
    """Check if trading volume increased over the past 2 days and show clear messages."""
    try:
        st.success("Trading Volume")

        url = f"https://api.coingecko.com/api/v3/coins/{coin_symbol}/market_chart?vs_currency=usd&days=2"
        r = requests.get(url)

        # --- Handle status codes clearly ---
        if r.status_code == 404:
            st.error("❌ Coin not found — please check the symbol (e.g., 'bitcoin', 'ethereum').")
            return
        elif r.status_code == 429:
            st.error("⏳ Too many requests — CoinGecko rate limit reached. Try again in a minute.")
            return
        elif r.status_code >= 500:
            st.error("⚠️ CoinGecko server error. Please try again later.")
            return
        elif r.status_code != 200:
            st.error(f"⚠️ Unexpected response (HTTP {r.status_code}).")
            return

        data = r.json()

        # --- Validate data ---
        if 'total_volumes' not in data or len(data['total_volumes']) < 2:
            st.warning("⚠️ Insufficient volume data available for this coin.")
            return

        vol_now = data['total_volumes'][-1][1]
        vol_prev = data['total_volumes'][0][1]
        vol_inc = ((vol_now - vol_prev) / vol_prev * 100) if vol_prev else 0

        pump_msg = (
            "likely to last (🚀 significant volume)" if vol_inc > 50 else
            "could last (📈 moderate volume)" if vol_inc > 20 else
            "may be short-lived (💤 low volume)"
        )

        st.write(f"Volume {'increased' if vol_inc > 0 else 'unchanged'} by **{vol_inc:.2f}%** — Pump/dump {pump_msg}")

    except requests.exceptions.RequestException:
        st.error("🌐 Network error — please check your internet connection or try again later.")
    except Exception as e:
        st.error(f"⚠️ Unexpected error: {e}")

def liquidity_to_supply_ratio(vol_24h, circ_supply):
    ratio = vol_24h / circ_supply if circ_supply else 0
    st.success("Liquidity to Supply Ratio")
    st.metric("Liquidity to Supply Ratio", f"{ratio:.4f}", border=True)
    st.write("High liquidity" if ratio > 1 else "Low liquidity")

def price_vs_ath(price, ath):
    pct = ((price - ath) / ath) * 100
    st.success("Price vs ATH (All-Time High)")
    st.metric("Price vs ATH", f"{pct:.2f}%", border=True)

    if pct > 0:
        st.write(f"**{pct:.2f}% above ATH** - Strong bullish sentiment, possible overvaluation risk")
    else:
        st.write(f"**{abs(pct):.2f}% below ATH** - Room for recovery or weaker interest")

def price_vs_atl(price, atl):
    pct = ((price - atl) / atl) * 100
    st.success("Price vs ATL (All-Time Low)")
    st.metric("Price vs ATL", f"{pct:.2f}%", border=True)

    if pct > 0:
        st.write(f"**{pct:.2f}% above ATL** - Significant recovery, long-term growth potential")
    else:
        st.write(f"**{abs(pct):.2f}% below ATL** - Extreme bearish, high risk")

def fdv_vs_market_cap(fdv, mcap):
    ratio = fdv / mcap if mcap else 0
    st.success("FDV to Market Cap Ratio")
    st.metric("FDV to Market Cap Ratio", f"{ratio:.2f}", border=True)

    if ratio > 1:
        st.markdown("- **>1**: Not all tokens circulating, future dilution risk")
    elif ratio == 1:
        st.markdown("- **=1**: All tokens circulating, no dilution risk")
    else:
        st.markdown("- **<1**: Unusual, possible miscalculation")

def circulating_supply_vs_total_supply(circ, total):
    ratio = circ / total if total else 0
    st.success("Circulating Supply vs Total Supply")
    st.metric("Circulating vs Total Supply Ratio", f"{ratio:.6f}", border=True)

    if ratio < 0.999:
        st.write("🔄 More coins may be released, potential price impact")
    else:
        st.write("✅ Almost all tokens circulating, low dilution risk")

def get_tokenomist_stats(coin_id):
    st.markdown(f'[View Tokenomist for {coin_id}](https://tokenomist.ai/{coin_id})')

def embedTradingViewChart(coin_symbol):
    symbol = coin_symbol.split('|')[0]
    return f"""
    <div class="tradingview-widget-container">
        <div class="tradingview-widget-copyright">
            <a href="https://www.tradingview.com/chart/?symbol={symbol}" target="_blank">
                <span class="blue-text">Track {symbol} on TradingView</span>
            </a>
        </div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js" async>
        {{
            "symbols": [["{coin_symbol}"]],
            "chartOnly": false,
            "width": "100%",
            "locale": "en",
            "colorTheme": "light",
            "autosize": true,
            "showVolume": true,
            "showMA": true,
            "hideDateRanges": false,
            "hideMarketStatus": false,
            "hideSymbolLogo": false,
            "scalePosition": "right",
            "scaleMode": "Normal",
            "fontFamily": "-apple-system, BlinkMacSystemFont, Trebuchet MS, Roboto, Ubuntu, sans-serif",
            "fontSize": "7",
            "noTimeScale": false,
            "valuesTracking": "1",
            "changeMode": "price-and-percent",
            "chartType": "line",
            "maLineColor": "#00008B",
            "maLineWidth": 5,
            "maLength": 9,
            "headerFontSize": "medium",
            "lineWidth": 25,
            "lineType": 0,
            "dateRanges": ["1w|1", "1m|30", "3m|60", "12m|1D", "60m|1W", "all|1M"]
        }}
        </script>
    </div>
    """