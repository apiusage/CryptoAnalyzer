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
    response = get_coin_data()

    # ✅ Check status code
    if response.status_code != 200:
        # Try to get API error details (JSON) if available
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text[:300]  # fallback: show first 300 chars

        raise ValueError(
            f"⚠️ API request failed!\n"
            f"🔹 Status: {response.status_code} ({response.reason})\n"
            f"🔹 URL: {response.url}\n"
            f"🔹 Details: {error_detail}"
        )

    # ✅ Parse data
    data = response.json()
    if not data or not isinstance(data, list):
        raise ValueError("⚠️ API returned no data or wrong format. Please refresh.")

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
        st.markdown("[FOMC Rate Moves](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.htmlwatch-tool.html)")
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

def topIndicatorInfo():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.success("**Top Warning ✅**")
        st.markdown(f"""
        - <span style="background-color: yellow; font-weight:bold;">Pi Cycle (watch closely)</span> – signals BTC peak
        - <span style="background-color: yellow; font-weight:bold;">Puell Multiple (watch closely)</span> - miners rich > 2, buy < 0.5  
        - Mayer – price very high (> 2× 200-day MA)  
        - 4-Year MA – long-term overbought (> 3.5× 4-year MA)  
        - NUPL – most holders are winning (≥ 70%)  
        - MVRV – unrealized gains very high (≥ 3)  
        """, unsafe_allow_html=True)

    with col2:
        st.success("**Confirm**")
        st.write("""
        - **CBBI** – bull market strength  
        - **LTH Supply** – long-term holders coins  
        - **STH Supply** – new holders coins  
        - **Dominance** – BTC vs altcoins  
        - **Altcoin Season** – altcoins peaking
        """)

    with col3:
        st.success("**Secondary**")
        st.write("""
        - **RSI** – short-term overbought  
        - **Trend** – price direction  
        - **Rainbow** – visual price guide  
        - **Macro Oscillator** – momentum extremes  
        - **ETF flows** – funds in/out of BTC  
        - **Company BTC cost** – company BTC holdings
        """)

def get_investing_data():
    topIndicatorInfo()
    singles = [
        ("**Bull Market Peak Signals**", "https://www.coinglass.com/bull-market-peak-signals", 1000),
        ("**Pi Cycle Top Indicator**", "https://www.coinglass.com/pro/i/pi-cycle-top-indicator", 1000),
        ("**Bitcoin Exchange Balance**", "https://www.coinglass.com/Balance", 1000),
        ("**Bitcoin Rainbow Chart**", "https://charts.bitbo.io/rainbow/", 1000),
        ("**r/CryptoCurrency stats**", "https://subredditstats.com/r/CryptoCurrency", 2000),
    ]
    pairs = [
        ("https://www.coinglass.com/pro/i/CDRI", "https://www.coinglass.com/pro/i/RsiHeatMap"),
    ]

    # Create tabs for singles
    tabs = st.tabs([label for label, _, _ in singles])
    for tab, (label, url, height) in zip(tabs, singles):
        with tab:
            st.components.v1.iframe(url, height=height, scrolling=True)

    # Show pairs as before
    show_iframes(pairs, [])
    st.success("**USDT / USDC Dominance** - High USDT / USDC dominance = Traders and investors moving funds out of volatile assets (like BTC, ETH, altcoins) into stablecoins.")
    st.markdown("""
                - Keep 1M monthly charts for USDT.D, USDC.D, TOTAL, TOTAL2, TOTAL3 — ideal for spotting bull market tops.
                - **1M**: Best timeframe to analyze for a bull market top. Bull market tops develop over months, not days
                - **(1W, 1D)**: Shorter timeframes are noisy and show temporary fluctuations.
                """)

    colUSDT, colUSDC = st.columns(2)
    with colUSDT:
        components.html(embedTradingViewChart("CRYPTOCAP:USDT.D|1M"), height=450)
    with colUSDC:
        components.html(embedTradingViewChart("CRYPTOCAP:USDC.D|1M"), height=450)

    totalCol, total2Col, total3Col = st.columns(3)
    with totalCol:
        components.html(embedTradingViewChart("CRYPTOCAP:TOTAL|1M"), height=450)
    with total2Col:
        components.html(embedTradingViewChart("CRYPTOCAP:TOTAL2|1M"), height=450)
    with total3Col:
        components.html(embedTradingViewChart("CRYPTOCAP:TOTAL3|1M"), height=450)


def datamishInfo():
    # Data with exact trade durations
    data = {
        "Timeframe": ["360D – 180D", "90D", "30D", "14D", "7D", "2D", "24H", "12H", "6H", "4H", "2H", "1H"],
        "Trade Duration": [
            "2–12 months",
            "1–3 months",
            "2–4 weeks",
            "1–2 weeks",
            "4–7 days",
            "1–2 days",
            "12–24 hours",
            "6–12 hours",
            "3–6 hours",
            "2–4 hours",
            "1–2 hours",
            "30–60 minutes"
        ],
        "Use Case": [
            "Macro trend / cycle tops or bottoms",
            "Macro trend / swing trades",
            "Short-term swings, funding rate extremes",
            "Weekly sentiment, shorts/liquidation spikes",
            "Short swing trades, monitor BTC shorts & funding",
            "Intraday moves, liquidation events",
            "Short-term swing trades",
            "Intraday monitoring",
            "Intraday scalps / leverage shifts",
            "Short-term entries/exits",
            "Very short-term moves",
            "Ultra short-term scalping / fast BTC shorts & funding moves"
        ]
    }

    df = pd.DataFrame(data)

    # Define desired order (1H first, 360D last)
    order = ["1H", "2H", "4H", "6H", "12H", "24H", "2D", "7D", "14D", "30D", "90D", "360D – 180D"]
    df["Timeframe"] = pd.Categorical(df["Timeframe"], categories=order, ordered=True)
    df = df.sort_values("Timeframe").reset_index(drop=True)  # Reset index

    # Display as interactive datatable
    st.dataframe(df, width=1000)

def get_trading_data():
    col1, col2 = st.columns(2)
    with col1:
        datamishInfo()
    with col2:
        st.markdown("[Datamish](https://datamish.com/)")
        st.markdown("[Cryptoprediction](https://cryptoprediction.io/)")
    pairs = [
        ("https://www.coinglass.com/InflowAndOutflow","https://www.coinglass.com/whale-alert"),
        ("https://www.coinglass.com/large-orderbook-statistics","https://www.coinglass.com/pro/futures/LiquidationHeatMap"),
        ("https://www.coinglass.com/pro/options/max-pain","https://www.coinglass.com/liquidation-maxpain"),
        ("https://www.coinglass.com/pro/futures/TimeZoneDistribution", "https://www.coinglass.com/TopTrader/Binance")
    ]
    show_iframes(pairs, [])


def get_footer_data():
    # =============================
    # COLUMN 1 - Macro & On-Chain
    # =============================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.success("🌍 Check Accumulation Phase")
        st.markdown("[Dropstab](https://dropstab.com/tab/8kwolcb86m?slug=8kwolcb86m)")

        st.success("Token Unlock")
        st.markdown("[Tokenomist](https://tokenomist.ai/)")

        st.success("Github Activities")
        st.markdown("[Cryptomiso](https://www.cryptomiso.com/)")
        st.markdown("[DeveloperReport](https://www.developerreport.com/)")

        st.success("🌍 Macro Indicators")
        st.markdown("[DXY (U.S. Dollar Index)](https://www.tradingview.com/chart/?symbol=TVC%3ADXY)")
        st.write("📈 DXY up = U.S. Dollar strengthening vs crypto & stocks")
        st.markdown("[M2 Global Liquidity Index](https://www.tradingview.com/script/6JlXCXmW-M2-Global-Liquidity-Index/)")
        st.write("💧 Higher M2 = more liquidity")

        st.success("📊 On-Chain Indicators")
        st.markdown("[Bitcoin Address Count](https://studio.glassnode.com/charts/addresses.NewNonZeroCount)")
        st.markdown("[Bitcoin Active Addresses](https://www.bitcoinmagazinepro.com/charts/bitcoin-active-addresses/)")
        st.markdown("[Stock-to-Flow Model](https://www.bitcoinmagazinepro.com/charts/stock-to-flow-model/)")
        st.markdown("[Bitcoin: Terminal Price](https://www.lookintobitcoin.com/charts/terminal-price/)")
        st.markdown("[Altcoin Season Index](https://www.bitget.com/price/altcoin-season-index)")
        st.markdown("[HODL Waves](https://www.bitcoinmagazinepro.com/charts/hodl-waves/)")

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
        st.markdown("[OnChainFX](https://onchainfx.com/)")
        st.markdown("[CoinCheckup](https://coincheckup.com/)")
        st.markdown("[Coinalyze](https://coinalyze.net/)")
        st.markdown("[CoinRanking](https://coinranking.com/)")
        st.markdown("[Cryptobubbles](https://cryptobubbles.com/)")
        st.markdown("[Coincarp](https://www.coincarp.com/)")
        st.markdown("[SosoValue](https://sosovalue.com/)")
        st.markdown("[LookOnChain](https://www.lookonchain.com/index.aspx)")
        st.markdown("[Coinscan](https://www.coinscan.com/)")
        st.markdown("[Banter Bubbles](https://banterbubbles.com/)")

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
        st.markdown("[Avascan](https://avascan.info/)")
        st.markdown("[DEX Screener](https://dexscreener.com/)")

        st.success("📢 Sentiment & Community")
        st.markdown("[Fear & Greed Index](https://edition.cnn.com/markets/fear-and-greed)")
        st.markdown("[SwaggyStocks (WSB)](https://swaggystocks.com/dashboard/wallstreetbets/realtime)")

        st.success("🎥 Media & Social Stats")
        st.markdown("[InvestAnswers (Socialblade)](https://socialblade.com/youtube/channel/UClgJyzwGs-GyaNxUHcLZrkg)")
        st.markdown("[The EXACT Dates To Sell Bitcoin (Raoul Pal)](https://www.youtube.com/watch?v=QzY-WI1Edmg)")

        st.success("📚 Other Resources")
        st.markdown("[The Block Data](https://www.theblock.co/data/on-chain-metrics/bitcoin)")
        st.markdown("[Fred Economic Data](https://fred.stlouisfed.org/)")
        st.markdown("[Newhedge](https://newhedge.io/bitcoin)")

