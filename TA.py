import streamlit as st
import requests
from st_copy_to_clipboard import st_copy_to_clipboard

# Read the text file globally
with open("gpt_prompt.txt", "r", encoding="utf-8") as file:
    file_content = file.read()

def display_text_with_copy_button(coin_name):
    global file_content  # Declare the global variable so it can be modified

    # Replace the placeholder with the coin name
    updated_content = file_content.replace("{CoinName}", coin_name)
    # st.code(updated_content, language="None", wrap_lines = True)

    try:
        st.session_state.clipboard = updated_content
        st_copy_to_clipboard(updated_content)
    except Exception as e:
        st.error(f"An error occurred while copying to clipboard: {e}")

def get_coin_creation_date(coin_id):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
    response = requests.get(url)

    if response.status_code == 200:
        coin_data = response.json()
        creation_date = coin_data.get('genesis_date', 'Not available')
        st.metric(label="Creation Date", value=creation_date, border=True)
    else:
        return f"Error: {response.status_code}"

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
    ratio = total_volume / market_cap

    st.success("Liquidity and trading activity")
    st.metric(label="Vol. (24h) / MCap Ratio", value=f"{ratio:.4f}", delta=f"{(ratio*100):.2f}%", border=True)

    # Interpretation based on the ratio
    if ratio > 0.1:
        st.markdown("""
            - Interpretation: High Ratio (Active Trading, High Liquidity) > 0.1 (10%).
            - Actively traded relative to its market cap, indicating high liquidity.
            - Likely popular, well-known, or experiencing a surge due to news or market events.
            """)
    elif ratio > 0.01:
        st.markdown("""
            - Interpretation: Moderate Ratio (Moderate Activity and Liquidity) > 0.01 (1%)
            - Moderate liquidity, trading activity, potentially a stable coin.
            """)
    else:
        st.markdown("""
            - Interpretation: Low Ratio (Low Trading Activity, Low Liquidity)
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
        volume_increase = ((volume_24h - volume_24h_previous) / volume_24h_previous) * 100

        # Determine if the pump is likely to last based on the volume increase
        if volume_increase > 50:
            pump_likely = "The pump is likely to last due to a significant increase in trading volume."
        elif volume_increase > 20:
            pump_likely = "The pump could last, but further confirmation is needed (moderate volume increase)."
        else:
            pump_likely = "The pump may be short-lived, as the volume increase is not very significant."

        # Check if the trading volume has increased or not
        if volume_increase > 0:
            return f"Trading volume of {coin_symbol} has increased by {volume_increase:.2f}% in the last 24 hours.\n{pump_likely}"
        else:
            return f"Trading volume of {coin_symbol} has not increased in the last 24 hours."

    except requests.exceptions.RequestException as e:
        return f"Error fetching data: {e}"

def liquidity_to_supply_ratio(trading_volume_24h, circulating_supply):
    ratio = trading_volume_24h / circulating_supply
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
    ratio = fully_diluted_valuation / market_cap
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
    ratio = circulating_supply / total_supply
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