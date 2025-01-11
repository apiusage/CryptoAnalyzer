import streamlit as st

def get_technicals_stats(coin_symbol):
    technicals_url = (
        f"https://www.tradingview.com/symbols/{coin_symbol}/technicals/"
    )
    st.markdown(f'[View Tradingview Technicals for {coin_symbol}]({technicals_url})')


