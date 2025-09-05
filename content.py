import streamlit.components.v1 as components
from TA import *
from FA import *
from bs4 import BeautifulSoup

def sticky_scroll_to_top():
    # Put a hidden anchor at the very top of the page
    st.markdown("<a id='top'></a>", unsafe_allow_html=True)

    # Load external CSS
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Button HTML (kept inline)
    st.markdown('<a href="#top" id="scrollTopBtn">⬆️</a>', unsafe_allow_html=True)

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

def get_coin_table():
    # ✅ Fetch coin data
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

    # ✅ Fetch categories mapping
    coin_to_categories = get_coin_categories()

    # ✅ Initialize dataframe only once
    if "coins_df" not in st.session_state:
        coins_list = []
        for coin in st.session_state.coins_data:
            coin_id = coin.get("id")
            categories = coin_to_categories.get(coin_id, [])
            coins_list.append({
                "Select": False,
                "Rank": coin.get("market_cap_rank"),
                "Image": coin.get("image"),
                "Coin": coin.get("name"),
                "Symbol": coin.get("symbol", "").upper(),
                "Category": ", ".join(categories) if categories else "N/A"
            })

        st.session_state.coins_df = pd.DataFrame(coins_list)

        # Fill missing ranks with max+1
        st.session_state.coins_df["Rank"] = st.session_state.coins_df["Rank"].fillna(
            st.session_state.coins_df["Rank"].max() + 1
        )

    column_config = {
        "Select": st.column_config.CheckboxColumn(disabled=False),
        "Image": st.column_config.ImageColumn("Logo"),
        "Coin": st.column_config.TextColumn("Coin"),
        "Symbol": st.column_config.TextColumn("Symbol"),
        "Category": st.column_config.TextColumn("Category"),
    }

    col1, col2 = st.columns([2, 1])

    with col1:
        # --- Separate selected and unselected coins ---
        df_selected = st.session_state.coins_df[
            st.session_state.coins_df["Select"]
        ].sort_values("Rank")

        df_others = st.session_state.coins_df[
            ~st.session_state.coins_df["Select"]
        ].sort_values("Rank")

        # Combine selected on top, unselected below
        df_display = pd.concat([df_selected, df_others]).reset_index(drop=True)

        # --- Render editable table ---
        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config=column_config,
            key="coins_table_editor"
        )

        # --- Detect changes and update session state ---
        changed = False
        for sym, sel in zip(edited_df["Symbol"], edited_df["Select"]):
            prev_sel = st.session_state.coins_df.loc[
                st.session_state.coins_df["Symbol"] == sym, "Select"
            ].iloc[0]

            if sel != prev_sel:
                st.session_state.coins_df.loc[
                    st.session_state.coins_df["Symbol"] == sym, "Select"
                ] = sel
                changed = True

        # Only rerun if a checkbox actually changed
        if changed:
            st.rerun()

        # ✅ Selected coins
        selected_coins = st.session_state.coins_df.loc[
            st.session_state.coins_df["Select"], "Symbol"
        ].tolist()
        st.session_state.selected_coins = selected_coins

    with col2:
        st.write("### 🔎 Analyze with ChatGPT")
        if selected_coins:
            if st.button("Run GPT Analysis"):
                gpt_prompt_copy("coins_gpt_prompt.txt", "{coin_list}", str(selected_coins))

            st.write("### 🐦 Socials")
            gpt_prompt_copy_msg(
                "Create a table to show numbers of followers in descending order based on follower count:",
                " crypto coins",
                str(selected_coins),
            )
        else:
            st.info("👉 Select coins first.")

    # Select/Deselect all
    colA, colB = st.columns([0.3, 1])
    with colA:
        if st.button("Select All"):
            st.session_state.coins_df["Select"] = True
            st.rerun()

    with colB:
        if st.button("Deselect All"):
            st.session_state.coins_df["Select"] = False
            st.rerun()

    return selected_coins


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

def show_iframes(pairs=None, singles=None):
    if singles:
        # if user passed a string → wrap in list
        if isinstance(singles, str):
            singles = [(singles, 2000)]
        for url, h in singles:
            components.html(f'<iframe src="{url}" width=100% height="{h}" style="border:none" loading="lazy"></iframe>', height=h)
    if pairs:
        for l, r in pairs:
            c1, c2 = st.columns(2)
            with c1:
                components.html(f'<iframe src="{l}" width=100% height="800px" style="border:none" loading="lazy"></iframe>', height=800)
            with c2:
                components.html(f'<iframe src="{r}" width=100% height="800px" style="border:none" loading="lazy"></iframe>', height=800)

def get_investing_data():
    singles = [
        ("https://www.coinglass.com/bull-market-peak-signals", 2000),
        ("https://www.coinglass.com/Balance", 2000),
    ]
    pairs = [
        ("https://www.coinglass.com/pro/i/CDRI", "https://www.coinglass.com/pro/i/RsiHeatMap"),
    ]

    show_iframes(pairs, singles)
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

def get_trading_data():
    pairs = [
        ("https://www.coinglass.com/InflowAndOutflow","https://www.coinglass.com/whale-alert"),
        ("https://cryptobubbles.net","https://www.coinglass.com/pro/futures/LiquidationHeatMap"),
        ("https://www.coinglass.com/pro/options/max-pain","https://www.coinglass.com/liquidation-maxpain"),
    ]
    show_iframes(pairs, "https://www.coinglass.com/spot-inflow-outflow")


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
        st.markdown("[Cryptoprediction](https://cryptoprediction.io/)")
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
        st.markdown("[Newhedge](https://newhedge.io/bitcoin)")

