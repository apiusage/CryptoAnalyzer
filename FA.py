# Whitepaper, Tokenomics, Team, Market Sentiment
import streamlit as st
import requests
import urllib
import pandas as pd
from datetime import datetime
from st_copy_to_clipboard import st_copy_to_clipboard

cmc_api_key = 'fcf7ee51-af70-4614-821a-f253d1f0d7da'  # CoinMarketCap API key

def gpt_prompt_copy(txt_file, placeholder, replacement, name="", key_suffix="", show_text=False):
    try:
        updated_content = open(txt_file, encoding="utf-8").read().replace(placeholder, replacement)
        st_copy_to_clipboard(
            updated_content,
            before_copy_label=f"📋 {name}" if name else "Copy Prompt",
            after_copy_label="✅ Text copied!",
            show_text=show_text,
            key=f"copy_{hash(replacement)}_{key_suffix}"
        )
    except Exception as e:
        st.error(f"Error copying to clipboard: {e}")

def gpt_prompt_copy_msg(prefixMsg, suffixMsg, coin_list):
    st_copy_to_clipboard(str(prefixMsg) + str(coin_list) + str(suffixMsg), before_copy_label="Copy Prompt", after_copy_label="✅ Text copied!")

# https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false
@st.cache_data(show_spinner=False)
def get_coin_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 200,
        'page': 1,
        'sparkline': 'false'
    }
    return requests.get(url, params=params)  # return raw response

@st.cache_data(show_spinner=False)
def get_coin_categories():
    url = "https://api.coingecko.com/api/v3/coins/categories"
    response = requests.get(url)
    categories = response.json()

    coin_to_categories = {}
    for cat in categories:
        name = cat.get("name")
        top_ids = cat.get("top_3_coins_id", [])
        for coin_id in top_ids:
            coin_to_categories.setdefault(coin_id, []).append(name)
    return coin_to_categories

def get_coin_creation_date(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    response = requests.get(url)

    if response.status_code == 200:
        coin_data = response.json()
        creation_date = coin_data.get('genesis_date', 'Not available')
        st.metric(label="Creation Date", value=creation_date, border=True)
    else:
        return f"Error: {response.status_code}"

def fetch_fng(api_source):
    # Define the common logic for processing timestamps and values
    def process_data(data):
        timestamps = [int(entry['timestamp']) for entry in data]
        values = [entry['value'] for entry in data]
        dates = [datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps]
        return pd.DataFrame({'Date': pd.to_datetime(dates), 'Fear and Greed Index': pd.to_numeric(values)})

    if api_source == "alternative_me":
        url = "https://api.alternative.me/fng/?limit=20"
        data = requests.get(url).json()['data']
        df = process_data(data)
        return df

    elif api_source == "coinmarketcap":
        url = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical"
        headers = {'X-CMC_PRO_API_KEY': cmc_api_key, 'Accept': 'application/json'}
        params = {'limit': 30, 'convert': 'USD'}
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()['data']
            df = process_data(data)
            return df
        else:
            st.error(f"Error: {response.status_code}")

    else:
        st.error("Invalid API source.")

def get_google_trends(coin_name, language="en"):
    # Handle spaces and special characters (eg. add '%20')
    encoded_coinName = urllib.parse.quote(coin_name)

    trends_url = (
        f"https://trends.google.com/trends/explore?&q={encoded_coinName}&hl={language}"
    )

    st.markdown(f'[View Google Trends for {coin_name}]({trends_url})')

def classify_market_cap(market_cap):
    if market_cap < 1_000_000:
        result = "Nano Cap - Market cap is less than $1 million."
    elif market_cap < 10_000_000:
        result = "Micro Cap - Market cap is between $1 million and $10 million."
    elif market_cap < 100_000_000:
        result = "Small Cap - Market cap is between $10 million and $100 million."
    else:
        result = "Large Cap - Market cap is greater than $100 million"

    st.success(result)

def calculate_vol_mcap_ratio(market_cap, total_volume):
    ratio = total_volume / market_cap if market_cap else 0

    st.success("Liquidity and trading activity - >30% = Buy")
    st.metric(label="Vol. (24h) / MCap Ratio", value=f"{ratio:.4f}", delta=f"{(ratio*100):.2f}%", border=True)

    # Interpretation based on the ratio
    if ratio > 0.1:
        st.markdown("""
            - High Ratio (Active Trading, High Liquidity) > 0.1 (10%).
            - Actively traded relative to its market cap, indicating high liquidity.
            - Likely popular, well-known, or experiencing a surge due to news or market events.
            """)
    elif ratio > 0.01:
        st.markdown("""
            - Moderate Ratio (Moderate Activity and Liquidity) > 0.01 (1%)
            - Moderate liquidity, trading activity, potentially a stable coin.
            """)
    else:
        st.markdown("""
            - Low Ratio (Low Trading Activity, Low Liquidity)
            - Limited trading activity, low liquidity. Not be as popular or may be held by long-term investors.
            - Could signal risks of price slippage for large trades.
            """)

def check_increased_trading_volume(coin_symbol):
    try:
        url = f'https://api.coingecko.com/api/v3/coins/{coin_symbol}/market_chart?vs_currency=usd&days=2'

        st.success("Trading Volume")
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception if the request failed
        data = response.json()

        # Extract trading volumes for the last 24 hours
        volume_24h = data['total_volumes'][1][1]  # Current 24h volume
        volume_24h_previous = data['total_volumes'][0][1]  # Previous 24h volume

        # Calculate the percentage increase in volume
        volume_increase = ((volume_24h - volume_24h_previous) / volume_24h_previous * 100) if volume_24h_previous else 0

        # Determine if the pump is likely to last based on the volume increase
        if volume_increase > 50:
            pump_likely = "The pump/dump is likely to last due to a significant increase in trading volume."
        elif volume_increase > 20:
            pump_likely = "The pump/dump could last, but further confirmation is needed (moderate volume increase)."
        else:
            pump_likely = "The pump/dump may be short-lived, as the volume increase is not very significant."

        # Check if the trading volume has increased or not
        if volume_increase > 0:
            st.write(f"Trading volume of {coin_symbol} has increased by **{volume_increase:.2f}%** in the last 24 hours.\n{pump_likely}")
        else:
            st.write(f"Trading volume of {coin_symbol} has not increased in the last 24 hours.")

    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

def liquidity_to_supply_ratio(trading_volume_24h, circulating_supply):
    ratio = trading_volume_24h / circulating_supply if circulating_supply else 0
    st.success("Liquidity to Supply Ratio")
    st.metric(label="Liquidity to Supply Ratio", value=f"{ratio:.4f}", border=True)
    if ratio > 1:
        st.write(f"High liquidity with significant trading volume relative to circulating supply.")
    else:
        st.write(f"Low liquidity with less trading activity compared to the circulating supply.")

# Function for Price vs ATH (All-Time High)
def price_vs_ath(current_price, ath):
    percent_difference = ((current_price - ath) / ath) * 100

    st.success("Price vs ATH (All-Time High)")
    st.metric(label="Price vs ATH", value=f"{percent_difference:.2f}%", border=True)

    if percent_difference > 0:
        st.write(f"Price is {percent_difference:.2f}% higher than its all-time high.")
        st.write(
            "This could indicate strong bullish sentiment and market demand. However, it may also pose risks of overvaluation or increased volatility.")
    else:
        st.write(f"Price is {abs(percent_difference):.2f}% lower than its all-time high.")
        st.write(
            "This suggests that the price is still below its historical peak, possibly indicating room for recovery or weaker market interest.")


# Function for Price vs ATH (All-Time High)
def price_vs_ath(current_price, ath):
    percent_difference = ((current_price - ath) / ath) * 100

    st.success("Price vs ATH (All-Time High)")
    st.metric(label="Price vs ATH", value=f"{percent_difference:.2f}%", border=True)

    if percent_difference > 0:
        st.write(f"Price is {percent_difference:.2f}% higher than its all-time high.")
        st.write(
            "This could indicate strong bullish sentiment and market demand. However, it may also pose risks of overvaluation or increased volatility.")
    else:
        st.write(f"Price is {abs(percent_difference):.2f}% lower than its all-time high.")
        st.write(
            "This suggests that the price is still below its historical peak, possibly indicating room for recovery or weaker market interest.")


# Function for Price vs ATL (All-Time Low)
def price_vs_atl(current_price, atl):
    percent_increase = ((current_price - atl) / atl) * 100

    st.success("Price vs ATL (All-Time Low)")
    st.metric(label="Price vs ATL", value=f"{percent_increase:.2f}%", border=True)

    if percent_increase > 0:
        st.write(f"Price is up {percent_increase:.2f}% from its all-time low.")
        st.write(
            "This shows significant recovery or growth from its lowest point. It may indicate the cryptocurrency's potential for long-term growth.")
    else:
        st.write(f"Price is {abs(percent_increase):.2f}% below its all-time low.")
        st.write(
            "This is rare but suggests extreme bearish conditions or market inefficiencies, and the asset may be undervalued but carry high risks.")

def fdv_vs_market_cap(fully_diluted_valuation, market_cap):
    ratio = fully_diluted_valuation / market_cap if market_cap else 0
    st.success("FDV to Market Cap Ratio")
    st.metric(label="FDV to Market Cap Ratio", value=f"{ratio:.2f}", border=True)

    if ratio > 1:
        st.markdown("""
            - More than 1 (Not all tokens are in circulation yet)
            - Future release of tokens (e.g., through mining or vesting schedules) could dilute the value of currently circulating tokens, potentially impacting price.
            """)
    elif ratio == 1:
        st.markdown("""
            - Equals to 1 (All tokens are already in circulation)
            - There is no risk of future dilution, and the current Market Cap fully reflects the total supply.
            """)
    else:
        st.markdown("""
            - Less than 1 (Unusual and may occur if the circulating supply is miscalculated or the tokenomics are atypical.)
            - Current Market Cap closely reflects the value of circulating tokens.
            """)

def circulating_supply_vs_total_supply(circulating_supply, total_supply):
    ratio = circulating_supply / total_supply if total_supply else 0
    st.success("Circulating Supply vs Total Supply")
    st.metric(label="Circulating vs Total Supply Ratio", value=f"{ratio:.6f}", border=True)

    if ratio < 1:
        st.write("🔄 Less than 100% of the total supply is circulating.")
        st.write(
            "This suggests more coins may be released over time, which could impact the price depending on demand.")
    elif ratio >= 0.999 and ratio < 1:
        st.write("✅ The circulating supply is very close to the total supply.")
        st.write("This indicates almost all tokens are in circulation, leaving little room for inflation.")
    else:
        st.write("✅ All or nearly all of the total supply is already in circulation.")
        st.write("This makes the supply highly predictable and reduces the risk of dilution.")

def get_tokenomist_stats(coin_id):
    tokenomist_url = (
        f"https://tokenomist.ai/{coin_id}"
    )
    st.markdown(f'[View Tokenomist for {coin_id}]({tokenomist_url})')

# Updated embed function
# https://www.tradingview.com/widget-docs/widgets/charts/symbol-overview/
def embedTradingViewChart(coin_symbol):
    # Format the coin symbol properly for TradingView
    html_code = f"""
    <!-- TradingView Widget BEGIN -->
    <div class="tradingview-widget-container">

        <div class="tradingview-widget-copyright">
            <a href="https://www.tradingview.com/chart/?symbol={coin_symbol.split('|')[0]}" target="_blank">
                <span class="blue-text">Track {coin_symbol.split('|')[0]} on TradingView</span>
            </a>
        </div>

        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js" async>
        {{
            "symbols": [
                [
                    "{coin_symbol}"
                ]
            ],
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
            "dateRanges": [
                "1w|1",
                "1m|30",
                "3m|60",
                "12m|1D",
                "60m|1W",
                "all|1M"
            ]
        }}
        </script>
    </div>
    <!-- TradingView Widget END -->
    """
    return html_code

