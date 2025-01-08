# streamlit run main.py
import streamlit as st
import requests
import pandas as pd
from TA import *
from FA import *
from marketSentiment import *

# https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false
def get_coin_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 10,  # Number of coins to display
        'page': 1,
        'sparkline': 'false'
    }
    response = requests.get(url, params=params)
    return response.json()

def calculate_score(coin_symbol):
    return check_increased_trading_volume(coin_symbol)

def get_action(score):
    if score > 50:
        return "Entry"
    else:
        return "Exit"

def main():
    st.title("Coin Analyzer")

    # Check if coin data is already fetched in session state
    if "coins_data" not in st.session_state:
        st.session_state.coins_data = get_coin_data()

    coins_list = []
    for coin in st.session_state.coins_data:
        coins_list.append({
            "Select": False,  # Initialize checkbox state as False
            "Image": coin['image'] if isinstance(coin, dict) else None,
            "Coin": coin['name'] if isinstance(coin, dict) else None,
            "Symbol": coin['symbol'] if isinstance(coin, dict) else None,
        })

    df = pd.DataFrame(coins_list)

    # Initialize session state for checkbox values if not already initialized
    if "checkbox_values" not in st.session_state:
        st.session_state.checkbox_values = {index: False for index in range(len(df))}

    # Define column configuration for the DataFrame
    column_config = {
        "Select": st.column_config.CheckboxColumn(disabled=False),
        "Image": st.column_config.ImageColumn(),
        "Coin": st.column_config.TextColumn(),
        "Symbol": st.column_config.TextColumn(),
    }

    # Display the table with the image column and checkbox configured
    edited_df = st.data_editor(df, use_container_width=True, column_config=column_config, hide_index=True)

    # Update session state with checkbox values
    for idx, row in edited_df.iterrows():
        st.session_state.checkbox_values[idx] = row['Select']

    # Collect the selected coins (where checkbox is True)
    selected_coins = [df['Symbol'][i] for i in range(len(df)) if st.session_state.checkbox_values[i]]

    # Show selected coins
    st.write("Selected Coins:")
    st.write(selected_coins)

    # Initialize expander states in session_state
    if "expanders_state" not in st.session_state:
        st.session_state.expanders_state = {}

    if st.button("Start Analysis", type="primary"):
        for coin in st.session_state.coins_data:
            for coinSymbol in selected_coins:
                if coinSymbol.lower() == coin['symbol'].lower():
                    expander_key = f"expander_{coin['name']}"

                    # Set expander state dynamically based on session_state
                    expanded = st.session_state.expanders_state.get(expander_key, False)

                    # Create expander with the saved state
                    with st.expander(f"**{coin['symbol'].upper()}**", expanded=expanded):
                        # Update expander state when user interacts
                        st.session_state.expanders_state[expander_key] = True

                        col1, col2 = st.columns(2)
                        with col1:
                            get_coin_creation_date(coin['id'])
                        with col2:
                            display_text_with_copy_button(coin['name'])

                        classify_market_cap(coin['market_cap'])

                        a, b = st.columns(2)
                        c, d = st.columns(2)
                        a.metric("Market Cap Rank", coin["market_cap_rank"], "", border=True)
                        b.metric("Price Change (24h)", f"{coin['price_change_24h']:.2f} USD",
                                 f"{coin['price_change_percentage_24h']:.2f}%", border=True)
                        c.metric("ATH Change %", f"{coin['ath_change_percentage']:.2f}%", "", border=True)
                        d.metric("ATL Change %", f"{coin['atl_change_percentage']:.2f}%", "", border=True)

                        st.write(calculate_score(coin['id'].lower()))
                        # embed_google_trends_chart(str(coin['name']) + " coin")
                        calculate_vol_mcap_ratio(coin['market_cap'], coin['total_volume'])
                        fdv_vs_market_cap(coin['fully_diluted_valuation'], coin['market_cap'])
                        circulating_supply_vs_total_supply(coin['circulating_supply'], coin['total_supply'])
                        price_vs_ath(coin['current_price'], coin['ath'])
                        price_vs_atl(coin['current_price'], coin['atl'])
                        liquidity_to_supply_ratio(coin['total_volume'], coin['circulating_supply'])


# Run the app
if __name__ == "__main__":
    main()
