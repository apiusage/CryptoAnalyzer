# streamlit run main.py
from PIL import Image
from TA import *
from FA import *
from content import *

img = Image.open("images/bitcoin.png").convert('RGB').save('images/bitcoin.jpeg')
PAGE_CONFIG = {"page_title": "Crypto Analyzer", "page_icon":img, "layout":"wide", "initial_sidebar_state": "expanded" }
st.set_page_config(**PAGE_CONFIG)

LOGO_BANNER = """
<div style="
    background: linear-gradient(90deg, #0f2027, #203a43, #2c5364);
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
    text-align: center;
">
    <h1 style="
        color: #f1f1f1;
        font-family: 'Trebuchet MS', sans-serif;
        font-size: 2.2em;
        letter-spacing: 2px;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.6);
        margin: 0;
    ">
        🚀 Crypto Analyzer 📊
    </h1>
</div>
"""

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def main():
    components.html(LOGO_BANNER)
    selected_coins = get_coin_table()
    getcontent(selected_coins)
    coin_base_ranking()
    rainbowChart()
    getfng()
    getsubcontent()
    get_footer_data()

# Run the app
if __name__ == "__main__":
    main()
