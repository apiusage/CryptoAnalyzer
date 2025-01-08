import streamlit as st
from pytrends.request import TrendReq

# https://pypi.org/project/pytrends/
def get_google_trends(coin_name):
    pytrends = TrendReq(hl='en-US', tz=360)
    pytrends.build_payload([coin_name], cat=0, timeframe='now 7-d', geo='')
    interest_over_time_df = pytrends.interest_over_time()
    return interest_over_time_df


def embed_google_trends_chart(keyword: str, geo: str = "US", timeframe: str = "now%207-d", language: str = "en"):
    """
    Embed a Google Trends chart in Streamlit via an iframe workaround.

    Args:
        keyword (str): The keyword to search for.
        geo (str): The geographical region (default: "US").
        timeframe (str): The timeframe for the trends data (default: "now 7-d").
        language (str): The language setting for Google Trends (default: "en").
    """
    # Construct the URL for embedding
    trends_url = (
        f"https://trends.google.com/trends/explore?"
        f"date={timeframe}&q={keyword}&geo={geo}&hl={language}")

    try:
        # Attempt to embed the iframe in Streamlit
        iframe_html = f"""
            <iframe src="{trends_url}" width="100%" height="600" frameborder="0"></iframe>
        """
        st.components.v1.html(iframe_html, height=600)

    except Exception as e:
        # Catch any exceptions and display the error message
        st.write(f"An error occurred while embedding Google Trends: {e}")
        st.write(f"URL: {trends_url}")
