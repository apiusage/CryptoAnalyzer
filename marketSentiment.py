import urllib
from datetime import datetime
import streamlit as st
import requests
import pandas as pd

def fetch_and_plot_fear_and_greed():
    # Fetch data from the API
    url = "https://api.alternative.me/fng/?limit=20"
    response = requests.get(url)
    data = response.json()['data']

    # Extract the relevant data from the response
    timestamps = [int(entry['timestamp']) for entry in data]  # Ensure timestamp is an integer
    values = [entry['value'] for entry in data]

    # Convert timestamps to readable datetime format
    dates = [datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps]

    # Create a DataFrame for easy plotting
    df = pd.DataFrame({
        'Date': pd.to_datetime(dates),
        'Fear and Greed Index': pd.to_numeric(values)
    })

    col1, col2 = st.columns(2)

    with col1:
        # Embed the image
        st.image("https://alternative.me/crypto/fear-and-greed-index.png", caption="Latest Crypto Fear & Greed Index")
    with col2:
        # Plotting the data as a line chart in Streamlit
        st.line_chart(df.set_index('Date'))


def fetch_and_plot_fear_and_greed_CMC():
    # Your CoinMarketCap API key
    api_key = 'fcf7ee51-af70-4614-821a-f253d1f0d7da'  # Replace with your actual API key
    url = "https://pro-api.coinmarketcap.com/v3/fear-and-greed/historical"

    # Define the headers for the API request
    headers = {
        'X-CMC_PRO_API_KEY': api_key,
        'Accept': 'application/json',
    }

    # Parameters for the historical data request (for the last 30 days, for example)
    params = {
        'limit': 30,  # Number of data points
        'convert': 'USD',  # Conversion to USD
    }

    # Fetch data from the CoinMarketCap API
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()['data']

        # Process the data into a DataFrame
        timestamps = [entry['timestamp'] for entry in data]
        values = [entry['value'] for entry in data]

        st.write(f"Value: {values[0]}")

        # Convert timestamps to readable datetime format
        dates = [datetime.utcfromtimestamp(int(ts)).strftime('%Y-%m-%d %H:%M:%S') for ts in timestamps]

        # Create a DataFrame for easy plotting
        df = pd.DataFrame({
            'Date': pd.to_datetime(dates),
            'Fear and Greed Index': pd.to_numeric(values)
        })

        st.line_chart(df.set_index('Date'))
    else:
        st.error(f"Error: {response.status_code}. Could not fetch data.")


# https://pypi.org/project/pytrends/
def get_google_trends(coin_name, timeframe="today 12-m", geo="Worldwide", language="en"):
    # Encode coin_name and timeframe to handle spaces and special characters add %20
    encoded_coinName = urllib.parse.quote(coin_name)
    # encoded_timeframe = urllib.parse.quote(timeframe)

    # Construct the URL for embedding
    trends_url = (
        f"https://trends.google.com/trends/explore?&q={encoded_coinName}&hl={language}"
    )

    # Create a clickable hyperlink in Streamlit
    st.markdown(f'[View Google Trends for {coin_name}]({trends_url})')






