import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from TA import *
from FA import *

def sticky_scroll_to_top():
    # Put a hidden anchor at the very top of the page
    st.markdown("<a id='top'></a>", unsafe_allow_html=True)

    # Floating button styled with CSS, links back to #top
    st.markdown(
        """
        <style>
        a#scrollTopBtn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            padding: 10px 16px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 10px;
            background: #4CAF50;
            color: white !important;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0,0,0,0.25);
            user-select: none;
            text-decoration: none;
        }
        a#scrollTopBtn:hover {
            filter: brightness(1.1);
        }
        html {
            scroll-behavior: smooth;
        }
        </style>

        <a href="#top" id="scrollTopBtn">⬇️</a>
        """,
        unsafe_allow_html=True
    )

# -------------------------------
# Helpers
# -------------------------------
@st.cache_data(ttl=300)
def get_coin_data_cached():
    data = get_coin_data()  # 🔹 Your existing API call
    if not data or not isinstance(data, list):
        raise ValueError("⚠️ Failed to fetch coin data. Please refresh.")
    return data


def deduplicate_coins(coins):
    """Keep only the first coin per symbol (ignore duplicates)."""
    seen = set()
    unique = []
    for coin in coins:
        sym = coin.get("symbol", "").upper()
        if sym not in seen:
            seen.add(sym)
            unique.append(coin)
    return unique


# -------------------------------
# Table UI
# -------------------------------
def get_coin_table():
    # ✅ Fetch with error handling
    if "coins_data" not in st.session_state:
        try:
            raw_data = get_coin_data_cached()
            st.session_state.coins_data = deduplicate_coins(raw_data)
        except Exception as e:
            st.error(f"❌ Could not load coins: {e}")
            return []

    if not st.session_state.coins_data:
        st.warning("⚠️ No coins available. Try refreshing.")
        return []

    # ✅ Initialize dataframe only once
    if "coins_df" not in st.session_state:
        coins_list = [
            {
                "Select": False,
                "Rank": coin.get("market_cap_rank"),
                "Image": coin.get("image"),
                "Coin": coin.get("name"),
                "Symbol": coin.get("symbol", "").upper(),
            }
            for coin in st.session_state.coins_data
        ]
        st.session_state.coins_df = pd.DataFrame(coins_list)

    # 👉 Display copy (sorted)
    df_display = (
        st.session_state.coins_df.sort_values(
            by=["Select", "Rank"], ascending=[False, True]
        ).reset_index(drop=True)
    )

    column_config = {
        "Select": st.column_config.CheckboxColumn(disabled=False),
        "Image": st.column_config.ImageColumn("Logo"),
        "Coin": st.column_config.TextColumn("Coin"),
        "Symbol": st.column_config.TextColumn("Symbol"),
    }

    homeCol1, homeCol2 = st.columns([2, 1])

    with homeCol1:
        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            key="coins_table",
        )

        # 🔥 Detect change in checkbox selection
        if not edited_df["Select"].equals(
            df_display["Select"]
        ):
            # Sync changes back
            for sym, sel in zip(edited_df["Symbol"], edited_df["Select"]):
                st.session_state.coins_df.loc[
                    st.session_state.coins_df["Symbol"] == sym, "Select"
                ] = sel

            # 👉 Force rerun immediately so sort reflects
            st.rerun()

    # ✅ Get selected coins
    selected_coins = st.session_state.coins_df.loc[
        st.session_state.coins_df["Select"], "Symbol"
    ].tolist()
    st.session_state.selected_coins = selected_coins

    with homeCol2:
        st.write("### 🔎 Analyze with ChatGPT")
        if selected_coins:
            if st.button("Run GPT Analysis"):
                gpt_prompt_copy("coins_gpt_prompt.txt", "{coin_list}", str(selected_coins))
                st.write("### 🐦 Socials")
                gpt_prompt_copy_msg(
                    "Create a table to show numbers of followers in descending order based on follower count:",
                    " crypto coins", str(selected_coins)
                )
        else:
            st.info("👉 Select coins first.")

    # ✅ Select/Deselect All
    colA, colB = st.columns(2)
    with colA:
        if st.button("Select All"):
            st.session_state.coins_df["Select"] = True
            st.session_state.selected_coins = st.session_state.coins_df["Symbol"].tolist()
            st.rerun()
    with colB:
        if st.button("Deselect All"):
            st.session_state.coins_df["Select"] = False
            st.session_state.selected_coins = []
            st.rerun()

    return selected_coins


# -------------------------------
# Content / Analysis UI
# -------------------------------
def getcontent(selected_coins):
    if not selected_coins:
        st.info("👉 Select coins and click Start Analysis.")
        return

    # ✅ Add session_state flag for button
    if "start_analysis" not in st.session_state:
        st.session_state.start_analysis = False

    if st.button("🚀 Start Analysis", type="primary"):
        st.session_state.start_analysis = True

    if st.session_state.start_analysis:
        for coin in st.session_state.coins_data:
            if coin["symbol"].upper() not in selected_coins:
                continue

            expander_key = f"expander_{coin['name']}"

            with st.expander(f"**{coin['symbol'].upper()}**", expanded=False):
                st.session_state[expander_key] = True

                col1, col2 = st.columns(2)
                with col1:
                    get_google_trends(coin["name"] + " coin")
                    get_technicals_stats(coin["symbol"])
                    get_tokenomist_stats(coin["id"])
                    st.image("images/redflag_token_distribution.jpg")
                    get_coin_creation_date(coin["id"])

                with col2:
                    st.write("### Fundamentals")
                    gpt_prompt_copy("individual_coin_gpt_prompt.txt", "{CoinName}", coin["name"])

                    st.write("### Price Prediction")
                    gpt_prompt_copy_msg(
                        f"Current price: {coin['current_price']}. "
                        "Give a worse and best scenario price prediction of ",
                        " crypto coin in months, years in table using market cap. "
                        "Consider it always way below bitcoin/eth market cap, etc. ",
                        coin["name"]
                    )

                classify_market_cap(coin["market_cap"])

                a, b = st.columns(2)
                c, d = st.columns(2)
                a.metric("Market Cap Rank", coin["market_cap_rank"], "", border=True)
                b.metric("Price Change (24h)", f"{coin['price_change_24h']:.2f} USD",
                         f"{coin['price_change_percentage_24h']:.2f}%", border=True)
                c.metric("ATH Change %", f"{coin['ath_change_percentage']:.2f}%", "", border=True)
                d.metric("ATL Change %", f"{coin['atl_change_percentage']:.2f}%", "", border=True)

                # Extra analytics
                check_increased_trading_volume(coin["id"].lower())
                calculate_vol_mcap_ratio(coin["market_cap"], coin["total_volume"])
                fdv_vs_market_cap(coin["fully_diluted_valuation"], coin["market_cap"])
                circulating_supply_vs_total_supply(coin["circulating_supply"], coin["total_supply"])
                price_vs_ath(coin["current_price"], coin["ath"])
                price_vs_atl(coin["current_price"], coin["atl"])
                liquidity_to_supply_ratio(coin["total_volume"], coin["circulating_supply"])


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

        u = "https://apps.apple.com/us/app/coinbase-buy-bitcoin-ether/id886427730"
        t = BeautifulSoup(requests.get(u, headers={"User-Agent": "Mozilla/5.0"}).text, "html.parser").find("a", {
            "class": "inline-list__item"}).get_text(strip=True)
        st.markdown(f"<h2 style='text-align:center'>📱 Coinbase App Store Rank {t}</h2>", unsafe_allow_html=True)


def get_investing_data():
    colBull, colBTCBal = st.columns(2)
    with colBull:
        components.html("""
        <iframe src="https://www.coinglass.com/bull-market-peak-signals" width=100% height="2000px" style="border: none" loading="lazy"></iframe>
        """, height=2000)

    with colBTCBal:
        components.html(
            '<iframe src="https://www.coinglass.com/Balance" '
            'width="100%" height="2000" style="border:none;" scrolling="yes"></iframe>',
            height=2000
        )

    colCDRI, colRSI = st.columns(2)
    with colCDRI:
        components.html("""
        <iframe src="https://www.coinglass.com/pro/i/CDRI" width=100% height="1500px" style="border: none" loading="lazy"></iframe>
        """, height=800)

    with colRSI:
        components.html("""
        <iframe src="https://www.coinglass.com/pro/i/RsiHeatMap" width=100% height="1500px" style="border: none" loading="lazy"></iframe>
        """, height=800)

    st.success("**USDT / USDC Dominance** - High USDT / USDC dominance = Traders and investors moving funds out of volatile assets (like BTC, ETH, altcoins) into stablecoins.")
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

    st.components.v1.iframe("https://charts.bitbo.io/rainbow/", height=800, scrolling=True)
    st.components.v1.iframe("https://dropstab.com/tab/8kwolcb86m?slug=8kwolcb86m", height=800, scrolling=True)


def get_trading_data():
    colInOutFlow, colWhaleAlert = st.columns(2)
    with colInOutFlow:
        components.html("""
        <iframe src="https://www.coinglass.com/InflowAndOutflow" width=100% height="800px" style="border: none" loading="lazy"></iframe>
        """, height=800)

    with colWhaleAlert:
        components.html("""
        <iframe src="https://www.coinglass.com/whale-alert" width=100% height="800px" style="border: none" loading="lazy"></iframe>
        """, height=800)

    colBubbles, colLiqHeatMap = st.columns(2)
    with colBubbles:
        components.html("""
        <iframe src="https://cryptobubbles.net" width=100% height="800px" style="border: none" loading="lazy"></iframe>
        """, height=800)

    with colLiqHeatMap:
        components.html("""
        <iframe src="https://www.coinglass.com/pro/futures/LiquidationHeatMap" width=100% height="800px" style="border: none" loading="lazy"></iframe>
        """, height=800)

    colMaxPain, colLiqMaxPain = st.columns(2)
    with colMaxPain:
        components.html("""
        <iframe src="https://www.coinglass.com/pro/options/max-pain" width=100% height="800px" style="border: none" loading="lazy"></iframe>
        """, height=800)

    with colLiqMaxPain:
        components.html("""
        <iframe src="https://www.coinglass.com/liquidation-maxpain" width=100% height="800px" style="border: none" loading="lazy"></iframe>
        """, height=800)

    components.html("""
          <iframe src="https://www.coinglass.com/spot-inflow-outflow" width=100% height="1500px" style="border: none" loading="lazy"></iframe>
          """, height=2000)


def get_footer_data():
    # =============================
    # COLUMN 1 - Macro & On-Chain
    # =============================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("🌍 Check Accumulation Phase")
        st.markdown("[Dropstab](https://dropstab.com/tab/8kwolcb86m?slug=8kwolcb86m)")

        st.success("🌍 Macro Indicators")
        st.markdown("[DXY (U.S. Dollar Index)](https://www.tradingview.com/chart/?symbol=TVC%3ADXY)")
        st.write("📈 DXY up = U.S. Dollar strengthening vs crypto & stocks")
        st.markdown("[M2 Global Liquidity Index](https://www.tradingview.com/script/6JlXCXmW-M2-Global-Liquidity-Index/)")
        st.write("💧 Higher M2 = more liquidity")

        st.success("📊 On-Chain Indicators")
        st.markdown("[Pi Cycle Top Indicator](https://charts.bitbo.io/pi-cycle-top/)")
        st.markdown("[MVRV Z-Score](https://www.coinglass.com/pro/i/bitcoin-mvrv-zscore)")
        st.markdown("[Mayer Multiple](https://charts.bitbo.io/mayermultiple/)")
        st.markdown("[Bitcoin Address Count](https://studio.glassnode.com/charts/addresses.NewNonZeroCount)")
        st.markdown("[Bitcoin Active Addresses](https://www.bitcoinmagazinepro.com/charts/bitcoin-active-addresses/)")
        st.markdown("[Rainbow Chart](https://www.blockchaincenter.net/en/bitcoin-rainbow-chart/)")
        st.markdown("[Stock-to-Flow Model](https://www.bitcoinmagazinepro.com/charts/stock-to-flow-model/)")
        st.markdown("[Altcoin Season Index](https://www.bitget.com/price/altcoin-season-index)")

    # =============================
    # COLUMN 2 - Analytics & Security
    # =============================
    with col2:
        st.success("🔍 Analytics Platforms")
        st.markdown("[Glassnode](https://studio.glassnode.com/home)")
        st.markdown("[CryptoQuant](https://cryptoquant.com/asset/btc/summary)")
        st.markdown("[Santiment](https://app.santiment.net/)")
        st.markdown("[Nansen](https://app.nansen.ai/)")
        st.markdown("[Laevitas](https://app.laevitas.ch/assets/home)")
        st.markdown("[Messari](https://messari.io/)")
        st.markdown("[DefiLlama](https://defillama.com/)")
        st.markdown("[Dune Analytics](https://dune.com/hildobby/btc-etfs)")
        st.markdown("[Lunarcrush](https://lunarcrush.com/categories/cryptocurrencies)")
        st.markdown("[CryptoSlate](https://cryptoslate.com/coins/)")
        st.markdown("[CryptoRank](https://cryptorank.io/)")
        st.markdown("[Tokenomist](https://tokenomist.ai/)")
        st.markdown("[OnChainFX](https://onchainfx.com/)")
        st.markdown("[CoinCheckup](https://coincheckup.com/)")
        st.markdown("[Coinalyze](https://coinalyze.net/)")
        st.markdown("[CoinRanking](https://coinranking.com/)")
        st.markdown("[SosoValue](https://sosovalue.com/)")
        st.markdown("[LookOnChain](https://www.lookonchain.com/index.aspx)")
        st.markdown("[Coinscan](https://www.coinscan.com/)")
        st.markdown("[DeveloperReport](https://www.developerreport.com/)")

        st.success("⚠️ Rugpull / Scam Detection")
        st.markdown("[Rugcheck](https://rugcheck.xyz)")
        st.markdown("[Token Sniffer](https://tokensniffer.com/)")
        st.markdown("[Sol Sniffer](https://www.solsniffer.com)")

    # =============================
    # COLUMN 3 - Explorers, Sentiment & Media
    # =============================
    with col3:
        st.success("🌐 Blockchain Explorers")
        st.markdown("[Etherscan](https://etherscan.io/)")
        st.markdown("[BSCScan](https://bscscan.com/)")
        st.markdown("[Solscan](https://solscan.io/)")
        st.markdown("[DEX Screener](https://dexscreener.com/)")

        st.success("📢 Sentiment & Community")
        st.markdown("[Fear & Greed Index](https://edition.cnn.com/markets/fear-and-greed)")
        st.markdown("[Crypto Subreddit Stats](https://subredditstats.com/r/CryptoCurrency)")
        st.markdown("[Banter Bubbles](https://banterbubbles.com/)")
        st.markdown("[SwaggyStocks (WSB)](https://swaggystocks.com/dashboard/wallstreetbets/realtime)")

        st.success("🎥 Media & Social Stats")
        st.markdown("[InvestAnswers (Socialblade)](https://socialblade.com/youtube/channel/UClgJyzwGs-GyaNxUHcLZrkg)")
        st.markdown("[The EXACT Dates To Sell Bitcoin (Raoul Pal)](https://www.youtube.com/watch?v=QzY-WI1Edmg)")

        st.success("📚 Other Resources")
        st.markdown("[FOMC Rate Moves](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.htmlwatch-tool.html)")
        st.markdown("[The Block Data](https://www.theblock.co/data/on-chain-metrics/bitcoin)")
        st.markdown("[Fred Economic Data](https://fred.stlouisfed.org/)")
        st.markdown("[Dropstab](https://dropstab.com/)")
        st.markdown("[Newhedge](https://newhedge.io/bitcoin)")

