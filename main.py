from PIL import Image
from pathlib import Path
import streamlit as st
from streamlit_option_menu import option_menu
from content import *
from TA import *
from unitTrust import *

# Move set_page_config OUTSIDE of any function and make it the FIRST Streamlit command
img_path = Path("images/bitcoin.jpeg")
if not img_path.exists():
    Image.open("images/bitcoin.png").convert("RGB").save(img_path)

st.set_page_config(
    page_title="AIO Analyzer",
    page_icon=Image.open(img_path),
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def setup():
    # Only cache non-config setup tasks
    st.markdown(f"<style>{Path('style.css').read_text()}</style>", unsafe_allow_html=True)

if __name__ == "__main__":
    setup()

    st.markdown("""
    <a href="/" target="_self" class="logo-banner">
        <h1><span class="emoji">🚀</span> AIO Analyzer <span class="emoji">📊</span></h1>
    </a>
    """, unsafe_allow_html=True)

    live_market_ticker()

    selected = option_menu(
        menu_title=None,
        options=["Investing", "Trading", "Coin Analyzer", "Unit Trust"],
        icons=["graph-up-arrow", "bar-chart", "coin", "piggy-bank-fill"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )

    if selected == "Investing":
        getfng()
        get_investing_data()
        get_footer_data()
        sticky_scroll_to_top()
    elif selected == "Trading":
        get_trading_data()
    elif selected == "Coin Analyzer":
        getcontent(get_coin_table())
    elif selected == "Unit Trust":
        unitTrustList([
            {"name": "Allianz Global Investors Fund - Allianz Income And Growth Am",
             "url": "https://www.investing.com/funds/allianz-income-growth-am-h2-technical"},
            {"name": "Pimco Gis Income Fund Administrative Sgd (hedged) Income",
             "url": "https://www.investing.com/funds/ie00b91rq825-technical"}
        ])