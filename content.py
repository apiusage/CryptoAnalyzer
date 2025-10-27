import streamlit.components.v1 as components
import re
from TA import *
from FA import *
import openpyxl

PROMPT_DIR = "prompts/"

def get_prompt_path(filename):
    return f"{PROMPT_DIR}{filename}"

def sticky_scroll_to_top():
    st.markdown("<a id='top'></a>", unsafe_allow_html=True)
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    st.markdown('<a href="#top" id="scrollTopBtn">⬆️</a>', unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_coin_data_cached():
    response = get_coin_data()
    if response.status_code != 200:
        try:
            error_detail = response.json()
        except:
            error_detail = response.text[:300]
        raise ValueError(f"⚠️ API failed! Status: {response.status_code} | {error_detail}")

    data = response.json()
    if not data or not isinstance(data, list):
        raise ValueError("⚠️ API returned no data. Please refresh.")
    return data

def deduplicate_coins(coins):
    seen = set()
    return [c for c in coins if (sym := c.get("symbol", "").upper()) not in seen and not seen.add(sym)]

def get_coin_table():
    # Initialize data
    if "coins_data" not in st.session_state:
        try:
            st.session_state.coins_data = deduplicate_coins(get_coin_data_cached())
        except Exception as e:
            st.error(f"❌ Could not load coins: {e}")
            return []

    if not st.session_state.coins_data:
        st.warning("⚠️ No coins available.")
        return []

    # Build dataframe once
    if "coins_df" not in st.session_state:
        coin_to_categories = get_coin_categories()
        coins_list = [{
            "Select": False,
            "Rank": c.get("market_cap_rank"),
            "Image": c.get("image"),
            "Coin": c.get("name"),
            "Symbol": c.get("symbol", "").upper(),
            "Category": ", ".join(coin_to_categories.get(c.get("id"), [])) or "N/A"
        } for c in st.session_state.coins_data]

        st.session_state.coins_df = pd.DataFrame(coins_list)
        st.session_state.coins_df["Rank"] = st.session_state.coins_df["Rank"].fillna(
            st.session_state.coins_df["Rank"].max() + 1
        )

    col1, col2 = st.columns([2, 1])

    with col1:
        # Sort: selected first
        df = st.session_state.coins_df
        df_display = pd.concat([
            df[df["Select"]].sort_values("Rank"),
            df[~df["Select"]].sort_values("Rank")
        ]).reset_index(drop=True)

        edited_df = st.data_editor(
            df_display,
            width='stretch',
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn(disabled=False),
                "Image": st.column_config.ImageColumn("Logo"),
            },
            key="coins_table_editor"
        )

        # Update selections
        for sym, sel in zip(edited_df["Symbol"], edited_df["Select"]):
            if sel != df.loc[df["Symbol"] == sym, "Select"].iloc[0]:
                df.loc[df["Symbol"] == sym, "Select"] = sel
                st.rerun()

        selected_coins = df.loc[df["Select"], "Symbol"].tolist()
        st.session_state.selected_coins = selected_coins

    with col2:
        st.write("### 🔎 Analyze with ChatGPT")
        if selected_coins:
            if st.button("Run GPT Analysis"):
                gpt_prompt_copy(get_prompt_path("coins_gpt_prompt.txt"), "{coin_list}", str(selected_coins))
            st.write("### 🐦 Socials")
            gpt_prompt_copy_msg("Create follower count table:", " crypto coins", str(selected_coins))
        else:
            st.info("👉 Select coins first.")

    # Bulk selection
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

    if "start_analysis" not in st.session_state:
        st.session_state.start_analysis = False

    if st.button("🚀 Start Analysis", type="primary"):
        st.session_state.start_analysis = True

    if st.session_state.start_analysis:
        for coin in st.session_state.coins_data:
            if coin["symbol"].upper() not in selected_coins:
                continue

            with st.expander(f"**{coin['symbol'].upper()}**", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    get_google_trends(coin["name"] + " coin")
                    get_technicals_stats(coin["symbol"])
                    get_tokenomist_stats(coin["id"])
                    st.image("images/redflag_token_distribution.jpg")
                    get_coin_creation_date(coin["id"])

                with col2:
                    st.write("### Fundamentals")
                    gpt_prompt_copy(get_prompt_path("individual_coin_gpt_prompt.txt"), "{CoinName}", coin["name"])
                    st.write("### Price Prediction")
                    gpt_prompt_copy_msg(
                        f"Current price: {coin['current_price']}. Worst/best scenario prediction for ",
                        " in months/years. Consider below BTC/ETH mcap.",
                        coin["name"]
                    )

                classify_market_cap(coin["market_cap"])

                a, b, c, d = st.columns(4)
                a.metric("MCap Rank", coin["market_cap_rank"], border=True)
                b.metric("24h Δ", f"{coin['price_change_24h']:.2f}", f"{coin['price_change_percentage_24h']:.2f}%",
                         border=True)
                c.metric("ATH Δ%", f"{coin['ath_change_percentage']:.2f}%", border=True)
                d.metric("ATL Δ%", f"{coin['atl_change_percentage']:.2f}%", border=True)

                # Analytics
                check_increased_trading_volume(coin["id"].lower())
                calculate_vol_mcap_ratio(coin["market_cap"], coin["total_volume"])
                fdv_vs_market_cap(coin["fully_diluted_valuation"], coin["market_cap"])
                circulating_supply_vs_total_supply(coin["circulating_supply"], coin["total_supply"])
                price_vs_ath(coin["current_price"], coin["ath"])
                price_vs_atl(coin["current_price"], coin["atl"])
                liquidity_to_supply_ratio(coin["total_volume"], coin["circulating_supply"])

def getfng():
    cols = st.columns(4)

    with cols[0]:
        df = fetch_fng("alternative_me")
        if not df.empty:
            current_value = df.iloc[0, 1]
            st.success(f"**FnG (alternative.me): {current_value} ({fng_label(current_value)})**")
            c1, c2 = st.columns(2)
            with c1:
                st.image("https://alternative.me/crypto/fear-and-greed-index.png")
            with c2:
                st.line_chart(df.set_index('Date'))

    with cols[1]:
        df = fetch_fng("coinmarketcap")
        if not df.empty:
            current_value = df.iloc[0, 1]
            st.success(f"**FnG (CMC): {current_value} ({fng_label(current_value)})**")
            st.line_chart(df.set_index('Date'))

    with cols[2]:
        st.markdown("[FOMC Rate Moves](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html)")
        sma_signal_table()

    with cols[3]:
        df = yf.download("BTC-USD", period="5y", interval="1wk", auto_adjust=True)
        display_unified_confidence_score(df)
        get_coinbase_app_rank()
        btc_weekly_dashboard_complete()

def show_iframes(pairs=None, singles=None):
    if singles:
        if isinstance(singles, str):
            singles = [(singles, 2000)]
        for url, h in singles:
            components.html(f'<iframe src="{url}" width=100% height="{h}" style="border:none"></iframe>', height=h)
    if pairs:
        for l, r in pairs:
            c1, c2 = st.columns(2)
            with c1:
                components.html(f'<iframe src="{l}" width=100% height="800" style="border:none"></iframe>', height=800)
            with c2:
                components.html(f'<iframe src="{r}" width=100% height="800" style="border:none"></iframe>', height=800)

def topIndicatorInfo():
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.success("**Prompts**")
        gpt_prompt_copy(
            txt_file=get_prompt_path("bitcoin_peak_prompt.txt"),
            placeholder="",
            replacement="",
            name="Top Warning History Prompt",
            key_suffix="1"
        )

        gpt_prompt_copy(
            txt_file=get_prompt_path("bitcoin_peak_prompt_grok.txt"),
            placeholder="",
            replacement="",
            name="Top Warning History Prompt (Grok)",
            key_suffix="2"
        )

    with col2:
        st.success("**Top Warning ✅**")
        st.markdown(f"""
        - <span style="background-color: yellow; font-weight:bold;">Pi Cycle (watch closely)</span> – signals BTC peak
        - <span style="background-color: yellow; font-weight:bold;">Puell Multiple (watch closely)</span> - miners rich > 2, buy < 0.5  
        - Mayer – price very high (> 2× 200-day MA)  
        - 4-Year MA – long-term overbought (> 3.5× 4-year MA)  
        - NUPL – most holders are winning (≥ 70%)  
        - MVRV – unrealized gains very high (≥ 3)  
        - Non-traders piling into meme coins, profits all over social media.  
        """, unsafe_allow_html=True)

    with col3:
        st.success("**Confirm**")
        st.write("""
        - **CBBI** – bull market strength  
        - **LTH Supply** – long-term holders coins  
        - **STH Supply** – new holders coins  
        - **Dominance** – BTC vs altcoins  
        - **Altcoin Season** – altcoins peaking
        """)

    with col4:
        st.success("**Secondary**")
        st.write("""
        - **RSI** – short-term overbought  
        - **Trend** – price direction  
        - **Rainbow** – visual price guide  
        - **Macro Oscillator** – momentum extremes  
        - **ETF flows** – funds in/out of BTC  
        - **Company BTC cost** – company BTC holdings
        """)

def show_df_with_avg(df, deline_col='deline', decline_col='Decline (%)'):
    df_display = df.copy()
    numeric_cols = df_display.select_dtypes('number').columns

    # Add average row at top
    avg_data = {col: df_display[col].mean() if col in numeric_cols else 'Average' if i == 0 else ''
                for i, col in enumerate(df_display.columns)}
    avg_row = pd.DataFrame([avg_data])
    df_display = pd.concat([avg_row, df_display], ignore_index=True)

    # Format numeric columns
    for col in numeric_cols:
        fmt = (lambda x, c=col: f"{int(round(x))}" if pd.notnull(x) else x) if col == deline_col \
            else (lambda x, c=col: f"{x:.2f}" if pd.notnull(x) else x)
        df_display[col] = df_display[col].apply(fmt)

    # Style function
    def highlight_rows(row):
        if row.name == 0:  # Average row
            return ['background-color: lightblue; font-weight: bold'] * len(row)
        return [
            'background-color: lightblue; font-weight: bold' if i == 0
            else 'background-color: yellow' if col in numeric_cols and col != decline_col and row[col] != '0.00'
            else ''
            for i, col in enumerate(df_display.columns)
        ]

    styled = df_display.style.apply(highlight_rows, axis=1).set_properties(**{'text-align': 'center'})
    st.dataframe(styled, use_container_width=True)

def get_investing_data():
    # Show top indicators first
    topIndicatorInfo()

    # Display Bitcoin Cycle Peaks Excel data below topIndicatorInfo
    file_path = "data/bitcoin_cycle_peaks.xlsx"
    try:
        # Load your Excel file
        df = pd.read_excel(file_path)
        show_df_with_avg(df)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
    except Exception as e:
        st.error(f"Error reading Excel file: {e}")

    # Define your other tabs (without Bitcoin Cycle Peaks)
    singles = [
        ("Bull Peak", "https://www.coinglass.com/bull-market-peak-signals", 1000),
        ("Pi Cycle", "https://www.coinglass.com/pro/i/pi-cycle-top-indicator", 1000),
        ("NUPL", "https://www.coinglass.com/pro/i/nupl", 1000),
        ("CDRI", "https://www.coinglass.com/pro/i/CDRI", 1000),
        ("RSI HeatMap", "https://www.coinglass.com/pro/i/RsiHeatMap", 1000),
        ("Exchange Balance", "https://www.coinglass.com/Balance", 1000),
        ("Rainbow", "https://charts.bitbo.io/rainbow/", 1000),
        ("r/CC Stats", "https://subredditstats.com/r/CryptoCurrency", 2000),
    ]

    tabs = st.tabs([label for label, _, _ in singles])
    for tab, (_, url, h) in zip(tabs, singles):
        with tab:
            st.components.v1.iframe(url, height=h, scrolling=True)

    # Existing USDT/USDC charts
    st.success("**USDT/USDC Dominance** - High = flight to stablecoins")
    st.markdown("**Use 1M charts** for bull tops (USDT.D, USDC.D, TOTAL, TOTAL2, TOTAL3)")

    col1, col2 = st.columns(2)
    with col1:
        components.html(embedTradingViewChart("CRYPTOCAP:USDT.D|1M"), height=450)
    with col2:
        components.html(embedTradingViewChart("CRYPTOCAP:USDC.D|1M"), height=450)

    c1, c2, c3 = st.columns(3)
    for col, chart in zip([c1, c2, c3], ["TOTAL", "TOTAL2", "TOTAL3"]):
        with col:
            components.html(embedTradingViewChart(f"CRYPTOCAP:{chart}|1M"), height=450)

def get_trading_data():
    col1, col2 = st.columns(2)
    with col1:
        data = {
            "Timeframe": ["1H", "2H", "4H", "6H", "12H", "24H", "2D", "7D", "14D", "30D", "90D", "360D-180D"],
            "Duration": ["30-60m", "1-2h", "2-4h", "3-6h", "6-12h", "12-24h", "1-2d", "4-7d", "1-2w", "2-4w", "1-3mo",
                         "2-12mo"],
            "Use": ["Scalp", "Short", "Entry/Exit", "Scalp", "Intraday", "Swing", "Intraday", "Swing", "Weekly",
                    "Swings", "Macro", "Cycle tops"]
        }
        st.dataframe(pd.DataFrame(data), width=1000)

    with col2:
        st.markdown("[Datamish](https://datamish.com/) | [Cryptoprediction](https://cryptoprediction.io/)")

    show_iframes([
        ("https://www.coinglass.com/InflowAndOutflow", "https://www.coinglass.com/whale-alert"),
        ("https://www.coinglass.com/large-orderbook-statistics",
         "https://www.coinglass.com/pro/futures/LiquidationHeatMap"),
        ("https://www.coinglass.com/pro/options/max-pain", "https://www.coinglass.com/liquidation-maxpain"),
        ("https://www.coinglass.com/pro/futures/TimeZoneDistribution", "https://www.coinglass.com/TopTrader/Binance")
    ])

def get_latest_shiller_pe():
    try:
        r = requests.get("https://www.multpl.com/shiller-pe", timeout=5)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        bold = soup.find("div", id="current").find("b")
        text = bold.next_sibling
        match = re.search(r"\d+\.?\d*", text)
        return match.group(0) if match else "N/A"
    except:
        return "N/A"

def indicator_guide(items):
    html = "<ul style='padding-left:18px;margin:0;'>"
    for label, desc, bg, fg in items:
        desc = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', desc)
        html += f"<li style='margin-bottom:6px;'><span style='background:{bg};color:{fg};font-weight:bold;padding:2px 6px;border-radius:4px;'>{label}</span> {desc}</li>"
    html += "</ul>"
    st.markdown(html, unsafe_allow_html=True)

def alert_box(msg, url, label="Learn more"):
    st.markdown(f"""
    <div style="padding:10px;background:#d4edda;color:#155724;border-radius:5px;">
        📢 {msg} = <a href="{url}" target="_blank" style="color:#155724;text-decoration:underline;">{label}</a>
    </div>
    """, unsafe_allow_html=True)

def get_footer_data():
    cols = st.columns(3)

    with cols[0]:
        st.success("🌍 Check Accumulation Phase")
        st.markdown("[Dropstab](https://dropstab.com/tab/8kwolcb86m?slug=8kwolcb86m)")

        st.success("Token Unlock")
        st.markdown("[Tokenomist](https://tokenomist.ai/)")

        st.success("Github Activities")
        st.markdown("[Cryptomiso](https://www.cryptomiso.com/) | [DeveloperReport](https://www.developerreport.com/)")

        st.success("🌍 Macro Indicators")
        st.markdown("[DXY](https://www.tradingview.com/chart/?symbol=TVC%3ADXY)")
        st.write("📈 DXY up = USD strengthening vs crypto")
        st.markdown("[M2 Liquidity](https://www.tradingview.com/script/6JlXCXmW-M2-Global-Liquidity-Index/)")
        st.write("💧 Higher M2 = more liquidity")
        st.markdown("[US PMI](https://www.tradingview.com/symbols/ECONOMICS-USBCOI/)")
        st.write("📈 >50 = growth, <50 = contraction")

        st.success("📊 On-Chain Indicators")
        st.markdown("[Address Count](https://studio.glassnode.com/charts/addresses.NewNonZeroCount)")
        st.markdown("[Active Addresses](https://www.bitcoinmagazinepro.com/charts/bitcoin-active-addresses/)")
        st.markdown("[Stock-to-Flow](https://www.bitcoinmagazinepro.com/charts/stock-to-flow-model/)")
        st.markdown("[Terminal Price](https://www.lookintobitcoin.com/charts/terminal-price/)")
        st.markdown("[Altcoin Season](https://www.bitget.com/price/altcoin-season-index)")
        st.markdown("[HODL Waves](https://www.bitcoinmagazinepro.com/charts/hodl-waves/)")

        st.success("🌐 Blockchain Explorers")
        st.markdown(
            "[Etherscan](https://etherscan.io/) | [BSCScan](https://bscscan.com/) | [Solscan](https://solscan.io/) | [Avascan](https://avascan.info/) | [DEX Screener](https://dexscreener.com/)")

    with cols[1]:
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
        st.markdown(
            "[Rugcheck](https://rugcheck.xyz) | [Token Sniffer](https://tokensniffer.com/) | [Sol Sniffer](https://www.solsniffer.com)")

        st.success("🎥 Media & Social Stats")
        st.markdown("[InvestAnswers](https://socialblade.com/youtube/channel/UClgJyzwGs-GyaNxUHcLZrkg)")
        st.markdown("[Raoul Pal - Sell Dates](https://www.youtube.com/watch?v=QzY-WI1Edmg)")

        st.success("📚 Other Resources")
        st.markdown("[The Block](https://www.theblock.co/data/on-chain-metrics/bitcoin)")
        st.markdown("[Fred Economic](https://fred.stlouisfed.org/)")
        st.markdown("[Newhedge](https://newhedge.io/bitcoin)")

    with cols[2]:
        alert_box("Market Crash Warning", "https://www.youtube.com/watch?v=MN5raca6oFA")

        shiller = get_latest_shiller_pe()
        st.markdown(f"[Market Valuation](https://www.currentmarketvaluation.com/) | [Multpl](https://www.multpl.com/)")
        st.markdown(f"[Buffett Indicator](https://en.macromicro.me/charts/406/us-buffet-index-gspc)")
        st.markdown(f"[Shiller PE: {shiller}](https://www.multpl.com/shiller-pe)")

        indicator_guide([
            ("Low <15", "**Undervalued**", "lightgreen", "black"),
            ("Avg ~16-17", "**Fairly valued**", "lightblue", "black"),
            ("High >25-30", "**Overvalued**", "orange", "black"),
            ("Warning >32", "**25-50% drop risk**", "firebrick", "white")
        ])

        st.markdown("[US Margin Debt](https://en.macromicro.me/charts/415/us-margin-debt)")
        st.markdown("[Yield Curve](https://www.slickcharts.com/treasury)")
        st.markdown("[WSJ Bonds](https://www.wsj.com/market-data/bonds)")

        indicator_guide([
            ("Upward", "Healthy economy", "lightgreen", "black"),
            ("Flat", "Uncertainty", "lightblue", "black"),
            ("Inverted", "Recession warning", "orange", "black")
        ])

        alert_box("Bond Market Crash", "https://www.youtube.com/watch?v=f9qPbjgFUj4")

        st.markdown("[Treasury IEI 3-7yr](https://www.tradingview.com/chart/?symbol=NASDAQ%3AIEI)")
        st.markdown("[Corporate LQD](https://www.tradingview.com/chart/?symbol=AMEX%3ALQD)")
        st.markdown("[PTY](https://www.tradingview.com/chart/?symbol=NYSE%3APTY)")
        st.markdown("[Maintenance vs Recessionary Cut](https://www.youtube.com/watch?v=f9qPbjgFUj4)")

        st.success("📢 Stock Market")
        st.markdown("[Fear & Greed](https://edition.cnn.com/markets/fear-and-greed)")
        st.markdown("[VIX Historical](https://www.macrotrends.net/2603/vix-volatility-index-historical-chart)")

        indicator_guide([
            ("Complacent", "<20", "lightgreen", "black"),
            ("Fearful", "20-39", "khaki", "black"),
            ("Panic", ">39", "crimson", "white")
        ])

        st.markdown("[SwaggyStocks](https://swaggystocks.com/dashboard/wallstreetbets/realtime)")
        st.markdown("[Finviz Map](https://finviz.com/map.ashx)")
        st.markdown("[Finviz Groups](https://finviz.com/groups.ashx)")
        st.markdown("[Stock Valuation](https://simplywall.st/stocks/us/semiconductors/nasdaq-nvda/nvidia/valuation)")
        st.markdown("[Earnings Calendar](https://earningshub.com/earnings-calendar/this-week)")

        st.success("📊 S&P 500 P/E Ratio")
        st.markdown("[90 Year Chart](https://www.macrotrends.net/2577/sp-500-pe-ratio-price-to-earnings-chart)")

        indicator_guide([
            ("Cheap", "<10", "lightgreen", "black"),
            ("Average", "~15-16", "lightblue", "black"),
            ("Fair", "15-20", "khaki", "black"),
            ("Expensive", ">20", "orange", "black"),
            ("Bubble", "30+ (1929, 2000)", "crimson", "white")
        ])

        st.success("📊 Put/Call Ratio")
        st.markdown("[CBOE Put/Call](https://en.macromicro.me/charts/449/us-cboe-options-put-call-ratio)")

        indicator_guide([
            ("Bullish", "<0.75", "lightgreen", "black"),
            ("Neutral", "~1", "lightblue", "black"),
            ("Bearish", ">1.5", "crimson", "white")
        ])

        st.success("📊 REITS")
        st.markdown("[CapitaLand Ascendas](https://www.tradingview.com/chart/?symbol=SGX%3AA17U)")
        st.markdown("[Frasers Centrepoint](https://www.tradingview.com/chart/?symbol=SGX%3AJ69U)")
        st.markdown("[CapitaLand ICT](https://www.tradingview.com/chart/?symbol=SGX%3AC38U)")
        st.markdown("[SPDR Homebuilders](https://www.tradingview.com/chart/?symbol=AMEX%3AXHB)")
        st.markdown("[Lowe's](https://www.tradingview.com/chart/?symbol=NYSE%3ALOW)")