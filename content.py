import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from TA import *
from FA import *

def get_coin_table():
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

    if st.button('Select All'):
        for idx in range(len(df)):
            st.session_state.checkbox_values[idx] = True  # Select all checkboxes

    # Collect the selected coins (where checkbox is True)
    selected_coins = [df['Symbol'][i] for i in range(len(df)) if st.session_state.checkbox_values[i]]
    # st.write("Selected Coins:")
    # st.write(selected_coins)
    return selected_coins

def getcontent(selected_coins):
    # Initialize expander states in session_state
    if "expanders_state" not in st.session_state:
        st.session_state.expanders_state = {}

    homeCol1, homeCol2 = st.columns(2)
    with homeCol1:
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
                                get_google_trends(str(coin['name']) + " coin")
                                get_technicals_stats(str(coin['symbol']))
                                get_coin_creation_date(coin['id'])
                            with col2:
                                st.write("Fundamentals analysis")
                                gpt_prompt_copy("individual_coin_gpt_prompt.txt", "{CoinName}", str(coin['name']))

                                st.write("Price prediction")
                                gpt_prompt_copy_msg(
                                    "Current price: " + str(coin['current_price']) + ". Give a worse and best scenario price prediction of ",
                                    " crypto coin in months, years in table using market cap. Consider it always way below bitcoin/eth market cap, etc. ",
                                    str(coin['name']))

                            classify_market_cap(coin['market_cap'])

                            a, b = st.columns(2)
                            c, d = st.columns(2)
                            a.metric("Market Cap Rank", coin["market_cap_rank"], "", border=True)
                            b.metric("Price Change (24h)", f"{coin['price_change_24h']:.2f} USD",
                                     f"{coin['price_change_percentage_24h']:.2f}%", border=True)
                            c.metric("ATH Change %", f"{coin['ath_change_percentage']:.2f}%", "", border=True)
                            d.metric("ATL Change %", f"{coin['atl_change_percentage']:.2f}%", "", border=True)

                            check_increased_trading_volume(coin['id'].lower())
                            # embed_google_trends_chart(str(coin['name']) + " coin")
                            calculate_vol_mcap_ratio(coin['market_cap'], coin['total_volume'])
                            fdv_vs_market_cap(coin['fully_diluted_valuation'], coin['market_cap'])
                            circulating_supply_vs_total_supply(coin['circulating_supply'], coin['total_supply'])
                            price_vs_ath(coin['current_price'], coin['ath'])
                            price_vs_atl(coin['current_price'], coin['atl'])
                            liquidity_to_supply_ratio(coin['total_volume'], coin['circulating_supply'])
    with homeCol2:
        st.write("Analyze coins using chatgpt")
        gpt_prompt_copy("coins_gpt_prompt.txt", "{coin_list}", str(selected_coins))

        st.write("Create table to show X account followers count")
        gpt_prompt_copy_msg("Create a table to show numbers of followers in descending order based on the follower count:", " crypto coins", str(selected_coins))

def getfng():
    # Fear and Greed Meter
    fng1Col, fng2Col, fng3Col = st.columns(3)
    with fng1Col:
        df = fetch_fng("alternative_me")
        st.success("**Fear and Greed Index (alternative.me): " + str(df.iloc[0, 1]) + "**")
        col1, col2 = st.columns(2)
        with col1: st.image("https://alternative.me/crypto/fear-and-greed-index.png",
                            caption="Latest Crypto Fear & Greed Index")
        with col2: st.line_chart(df.set_index('Date'))

    with fng2Col:
        df = fetch_fng("coinmarketcap")
        st.success("**Fear and Greed Index (CMC): " + str(df.iloc[0, 1]) + "**")
        st.line_chart(df.set_index('Date'))

    with fng3Col:
        st.markdown("""
                    - **0-25**: Extreme Fear (Market pessimism, buying opportunities for the long-term).
                    - **26-50**: Fear (Investor caution, potential opportunities in undervalued assets).
                    - **51-75**: Greed (Optimism, but market may be overheated. Consider profits or hedging).
                    - **76-100**: Extreme Greed / Euphoria (Bubble territory, extreme caution advised).
                    """)

def getsubcontent():
    st.success("**USDT / USDC Dominance** - High USDT / USDC dominance = Traders selling their cryptocurrencies")
    colUSDT, colUSDC = st.columns(2)
    with colUSDT:
        components.html(embedTradingViewChart("CRYPTOCAP:USDT.D|1M"), height=450)
    with colUSDC:
        components.html(embedTradingViewChart("CRYPTOCAP:USDC.D|1M"), height=450)

    totalCol, total2Col, total3Col = st.columns(3)
    with totalCol:
        components.html(embedTradingViewChart("CRYPTOCAP:TOTAL"), height=450)
    with total2Col:
        components.html(embedTradingViewChart("CRYPTOCAP:TOTAL2"), height=450)
    with total3Col:
        components.html(embedTradingViewChart("CRYPTOCAP:TOTAL3"), height=450)

    components.html("""
    <iframe src="https://cryptobubbles.net" width=100% height="800px" style="border: none" loading="lazy"></iframe>
    """, height=800)

    components.html("""
    <iframe src="https://banterbubbles.com/" width=100% height="800px" style="border: none" loading="lazy"></iframe>
    """, height=800)


def get_footer_data():
    # DXY
    st.success("DXY (U.S. Dollar Index)")
    st.markdown("[View DXY TradingView](https://www.tradingview.com/chart/?symbol=TVC%3ADXY)")
    st.write("DXY up = U.S. Dollar is strengthening relative to these other currencies (crypto, stocks..) ")

    # M2 Liquidity Index
    st.success("M2 Global Liquidity Index")
    st.markdown("[View M2 Global Liquidity Index on TradingView](https://www.tradingview.com/script/6JlXCXmW-M2-Global-Liquidity-Index/)")
    st.write("Higher M2 levels = more liquidity")

    statsCol, youtubeCol, otherCol = st.columns(3)
    with statsCol:
        st.success("Links")
        st.markdown("[FOMC Rate Moves](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.htmlwatch-tool.html)")
        st.markdown("[Rainbow Chart](https://www.blockchaincenter.net/en/bitcoin-rainbow-chart/)")
        st.markdown("[MVRV Z - Score](https://www.coinglass.com/pro/i/bitcoin-mvrv-zscore)")
        st.markdown("""
            - **MVRV > 1:** The asset is potentially overvalued.
            - **MVRV < 1:** The asset is potentially undervalued, could suggest a bottom or buying opportunity.
            - **MVRV = 1:** The asset is close to its fair value.
            - 🔵 Extreme Lows: MVRV has been Below 0.8 for around 5% of trading days.
            - 🟢 Getting Low: MVRV has been Below 1.0 for around 15% of trading days.
            - 🟠 Getting High: MVRV has been Above 2.4 for around 20% of trading days.
            - 🔴 Extremely High: MVRV has been Above 2.4 for around 6% of trading days.
            """)
        st.markdown("[Bitcoin Address Count](https://studio.glassnode.com/charts/addresses.NewNonZeroCount)")
        st.markdown("[ALT / BTC Season](https://www.bitget.com/price/altcoin-season-index)")
        st.markdown("[Crypto Subreddit Stats](https://subredditstats.com/r/CryptoCurrency)")

    with youtubeCol:
        st.success("Socialblade Stats")
        st.markdown("[InvestAnswers](https://socialblade.com/youtube/channel/UClgJyzwGs-GyaNxUHcLZrkg)")

    with otherCol:
        st.success("On-Chain Analysis")
        st.markdown("[Coinglass](https://www.coinglass.com/pro/i/pi-cycle-top-indicator)")
        st.markdown("[Glassnode](https://studio.glassnode.com/charts/addresses.ActiveCount?a=BTC)")
        st.markdown("[Cryptoquant](https://cryptoquant.com/asset/btc/summary)")
        st.markdown("[Blockchain](https://www.blockchain.com/explorer/charts/n-transactions)")

# def calculate_score(coin_symbol):
#   return check_increased_trading_volume(coin_symbol)

#def get_action(score):
#    if score > 50:
#        return "Entry"
#    else:
#       return "Exit"

