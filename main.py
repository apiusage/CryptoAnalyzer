from PIL import Image
from content import *
from streamlit_option_menu import option_menu
from pathlib import Path
from TA import *

# Convert PNG to JPEG properly
img = Image.open("images/bitcoin.png").convert("RGB")
img.save("images/bitcoin.jpeg")

PAGE_CONFIG = {
    "page_title": "AIO Analyzer",
    "page_icon": img,
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}
st.set_page_config(**PAGE_CONFIG)

# Inject CSS
st.markdown(f"<style>{Path('style.css').read_text()}</style>", unsafe_allow_html=True)

# Inline Banner
st.markdown(
    '<div class="logo-banner"><h1>🚀 <span style="color:#00ffc6;">Crypto / Stock / Bond / Reits Analyzer</span> 📊</h1></div>',
    unsafe_allow_html=True
)

# Show real-time, actionable market summary
mega_market_ticker_fixed()

def main():
    selected = option_menu(
        menu_title=None,
        options=["Investing", "Trading", "Coin Analyzer"],
        icons=["graph-up-arrow", "bar-chart", "coin"],
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
        selected_coins = get_coin_table()
        getcontent(selected_coins)

if __name__ == "__main__":
    main()