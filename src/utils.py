"""
This module contains utility functions for the stock analyzer.
"""

import pandas as pd
from pandas.tseries.offsets import BusinessDay  
from bs4 import BeautifulSoup
import requests
from pathlib import Path
from datetime import datetime, timedelta
from cloud_storage import cloud_storage

def get_trading_dates() -> tuple:
    """
    Returns the current trading date and the previous business day.
    Returns:
        tuple: (current_trading_date, previous_business_day)
    """
    # For now, return dummy dates
    current_trading_date = datetime.now().date()
    previous_business_day = current_trading_date - timedelta(days=1)
    return current_trading_date, previous_business_day


def load_or_download_sp500_tickers() -> pd.DataFrame:
    """
    Returns a DataFrame containing S&P 500 companies information.
    Uses cached data if available and not expired (1 day).
    
    Returns:
        pd.DataFrame: DataFrame with columns:
            - ticker: Stock symbol
            - security: Company name
            - sector: Business sector
            - industry: Industry classification
    """
    cache_file = 'sp500_cache.pkl'
    
    # Try to load from cloud cache
    cached_data = cloud_storage.load_from_cache(cache_file)
    if cached_data is not None:
        print(f"INFO: Using cached S&P 500 data from cloud storage")
        return cached_data
    
    print("INFO: Downloading fresh S&P 500 data from Wikipedia...")
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', {'id': 'constituents'})
    
    # Extract headers
    headers = [th.text.strip() for th in table.find_all('th')]
    
    # Extract data
    data = []
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) >= 4:  # Ensure we have all required columns
            data.append({
                'Ticker': cols[0].text.strip(),
                'Security': cols[1].text.strip(),
                'Sector': cols[2].text.strip(),
                'Industry': cols[3].text.strip()
            })
    
    result_df = pd.DataFrame(data)
    
    print("INFO: Saving S&P 500 data to cloud cache...")
    # Save to cloud cache
    cloud_storage.save_to_cache(result_df, cache_file)
    
    return result_df
