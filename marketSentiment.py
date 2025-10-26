import urllib.parse
from datetime import datetime
import streamlit as st
import requests
import pandas as pd

CMC_API_KEY = 'fcf7ee51-af70-4614-821a-f253d1f0d7da'

def process_fng_data(data):
    """Common processing for FNG data"""
    timestamps = [int(e['timestamp']) for e in data]
    values = [e['value'] for e in data]
    dates = [datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps]
    return pd.DataFrame({'Date': pd.to_datetime(dates), 'Fear and Greed Index': pd.to_numeric(values)})

def fetch_and_plot_fear_and_greed():
    data = requests.get("https://api.alternative.me/fng/?limit=20").json()['data']
    df = process_fng_data(data)

    col1, col2 = st.columns(2)
    with col1:
        st.image("https://alternative.me/crypto/fear-and-greed-index.png",
                 caption="Latest Crypto Fear & Greed Index")
    with col2:
        st.line_chart(df.set_index('Date'))

def fetch_and_plot_fear_and_greed_CMC():
    r = requests.get("https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical",
                     headers={'X-CMC_PRO_API_KEY': CMC_API_KEY, 'Accept': 'application/json'},
                     params={'limit': 30, 'convert': 'USD'})

    if r.status_code == 200:
        data = r.json()['data']
        df = process_fng_data(data)
        st.write(f"Value: {data[0]['value']}")
        st.line_chart(df.set_index('Date'))
    else:
        st.error(f"Error: {r.status_code}")

def get_google_trends(coin_name, language="en"):
    url = f"https://trends.google.com/trends/explore?&q={urllib.parse.quote(coin_name)}&hl={language}"
    st.markdown(f'[View Google Trends for {coin_name}]({url})')