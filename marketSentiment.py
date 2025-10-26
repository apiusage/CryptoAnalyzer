import urllib.parse
import streamlit as st

CMC_API_KEY = 'fcf7ee51-af70-4614-821a-f253d1f0d7da'

def get_google_trends(coin_name, language="en"):
    url = f"https://trends.google.com/trends/explore?&q={urllib.parse.quote(coin_name)}&hl={language}"
    st.markdown(f'[View Google Trends for {coin_name}]({url})')