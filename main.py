# streamlit run main.py
from PIL import Image
from TA import *
from content import *

img = Image.open("images/bitcoin.png").convert('RGB').save('images/bitcoin.jpeg')
PAGE_CONFIG = {"page_title": "Crypto Analyzer", "page_icon":img, "layout":"wide", "initial_sidebar_state": "expanded" }
st.set_page_config(**PAGE_CONFIG)

LOGO_BANNER = """
    <div style="background-color:#464e5f;padding:3px;border-radius:10px";>
    <h1 style="color:white;text-align:center;"> Crypto Analyzer </h1>
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
    getfng()
    getsubcontent()
    get_footer_data()

# Run the app
if __name__ == "__main__":
    main()
