from PIL import Image
from content import *
from streamlit_option_menu import option_menu

# Convert PNG to JPEG properly
img = Image.open("images/bitcoin.png").convert("RGB")
img.save("images/bitcoin.jpeg")

PAGE_CONFIG = {
    "page_title": "Crypto Analyzer",
    "page_icon": img,
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}
st.set_page_config(**PAGE_CONFIG)

# Inject custom CSS for blending
st.markdown("""
    <style>
    .logo-banner {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.4);
        text-align: center;
        margin-bottom: 0px;
    }
    .logo-banner h1 {
        color: #ffffff;
        font-family: 'Trebuchet MS', sans-serif;
        font-size: 2.2em;
        letter-spacing: 2px;
        text-shadow: 0 0 8px rgba(0,255,200,0.7),
                     0 0 20px rgba(0,255,200,0.5);
        margin: 0;
    }
    /* Style option menu to blend with banner */
    .nav.nav-pills {
        justify-content: center;
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        border-radius: 0 0 15px 15px;
        padding: 5px 0;
        margin-top: -5px;
    }
    .nav-link {
        color: #ddd !important;
        font-size: 18px;
        margin: 0 10px;
    }
    .nav-link.active {
        background-color: #00ffc6 !important;
        color: black !important;
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

LOGO_BANNER = """
    <div class="logo-banner">
        <h1>🚀 <span style="color:#00ffc6;">Crypto Analyzer</span> 📊</h1>
    </div>
"""

def main():
    # Show logo banner
    st.markdown(LOGO_BANNER, unsafe_allow_html=True)

    # Show blended menu
    selected = option_menu(
        menu_title=None,
        options=["Home", "Coin Analyzer"],
        icons=['house', 'reception-4'],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal"
    )

    # Content area
    if selected == "Home":
        getfng()
        getsubcontent()
        get_footer_data()
        sticky_scroll_to_top()
    elif selected == "Coin Analyzer":
        selected_coins = get_coin_table()
        getcontent(selected_coins)

if __name__ == "__main__":
    main()