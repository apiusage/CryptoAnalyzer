# streamlit run main.py
from PIL import Image
from TA import *
from FA import *
from content import *
import streamlit.components.v1 as components

img = Image.open("images/bitcoin.png").convert('RGB').save('images/bitcoin.jpeg')
PAGE_CONFIG = {"page_title": "Crypto Analyzer", "page_icon":img, "layout":"wide", "initial_sidebar_state": "expanded" }
st.set_page_config(**PAGE_CONFIG)

LOGO_BANNER = """
    <div style="
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
        text-align: center;
    ">
        <h1 style="
            color: #ffffff;
            font-family: 'Trebuchet MS', sans-serif;
            font-size: 2.2em;
            letter-spacing: 2px;
            text-shadow: 0 0 8px rgba(0,255,200,0.7),
                         0 0 20px rgba(0,255,200,0.5);
            margin: 0;
        ">
            🚀 <span style="color:#00ffc6;">Crypto Analyzer</span> 📊
        </h1>
    </div>
"""

def main():
    components.html(LOGO_BANNER)
    selected_coins = get_coin_table()
    getcontent(selected_coins)
    coin_base_ranking()
    rainbowChart()
    getfng()
    getsubcontent()
    get_footer_data()
    sticky_scroll_to_top()

# Run the app
if __name__ == "__main__":
    main()
