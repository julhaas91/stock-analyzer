"""
This module contains the main function to fetch the stock data and print the closing prices.
"""

from dotenv import load_dotenv
import yfinance as yf
from utils import load_or_download_sp500_tickers, get_trading_dates
import pandas as pd
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from cloud_storage import cloud_storage

load_dotenv()

def load_or_download_data(sp500_df: pd.DataFrame, previous_business_day: pd.Timestamp) -> pd.DataFrame:
    """
    Loads cached data if available and not expired, otherwise downloads new data.
    Cache expires after 1 day.

    Args:
        sp500_df: DataFrame containing S&P 500 stock information:
            - Ticker: Stock symbol
            - Security: Company name
            - Sector: Business sector
            - Industry: Industry classification
        previous_business_day: Previous business day as a pandas Timestamp object

    Returns:
        DataFrame containing stock data
    """
    cache_file = 'data_cache.pkl'
    
    # Try to load from cloud cache
    cached_data = cloud_storage.load_from_cache(cache_file)
    
    if cached_data is not None:
        print(f"INFO: Using cached STOCK data from cloud storage")
        return cached_data
    
    print("INFO: Downloading fresh stock data from yfinance...")
    data = yf.download(
        sp500_df['Ticker'].tolist(), 
        start=previous_business_day, 
        auto_adjust=False
    )
    
    print("INFO: Saving data to cloud cache...")
    cloud_storage.save_to_cache(data, cache_file)
    
    return data

def fetch_stock_data() -> pd.DataFrame:
    """
    Fetches the stock data for the S&P 500 stocks for the previous business day.
    Returns:
        DataFrame with columns:
            - Date: Trading date
            - Ticker: Stock symbol
            - Security: Company name
            - Sector: Business sector
            - Industry: Industry classification
            - Close: Closing price
    """
    sp500_df = load_or_download_sp500_tickers()
    # _, previous_business_day = get_trading_dates()
    # hardcode previous business day to 3 days ago
    previous_business_day = datetime.now().date() - timedelta(days=3)
    
    # Load cached data or download new data
    data = load_or_download_data(sp500_df, previous_business_day)
    
    # Get closing prices and convert to DataFrame
    closing_prices = data['Close'].stack().reset_index()
    closing_prices.columns = ['Date', 'Ticker', 'Close']
    
    # Merge with company information
    result_df = pd.merge(
        closing_prices,
        sp500_df,
        on='Ticker',
        how='left'
    )
    
    # Sort by date and ticker
    return result_df.sort_values(['Ticker', 'Date'])


def fetch_200_wk_simple_moving_average_SMA() -> pd.DataFrame:
    """
    Fetches the 200 week simple moving average for the S&P 500 stocks.
    Uses cached data if available and not expired (1 day).
    
    Returns:
        DataFrame with columns:
            - ticker: Stock symbol
            - 200wk_sma: 200-week simple moving average
            - % Deviation: Deviation from 200wk_sma
    """
    cache_file = '200wma_cache.pkl'
    
    # Try to load from cloud cache
    cached_data = cloud_storage.load_from_cache(cache_file)
    
    if cached_data is not None:
        print(f"INFO: Using cached 200wk_sma data from cloud storage")
        return cached_data
    
    print("INFO: Downloading fresh 200wk_sma data from yfinance...")
    sp500_df = load_or_download_sp500_tickers()
    end_date = datetime.now().date() - timedelta(days=3)
    start_date = end_date - timedelta(days=200*7 + 1) 
    
    data = yf.download(
        sp500_df['Ticker'].tolist(), 
        start=start_date, 
        end=end_date, 
        interval='1wk', 
        auto_adjust=False
    )
    
    closing_prices = data['Close'].T.round(2)
    closing_prices['200wk_sma'] = closing_prices.mean(axis=1).round(2)
    closing_prices['% Deviation'] = ((closing_prices.iloc[:, -2] - closing_prices['200wk_sma']) / closing_prices['200wk_sma']) * 100
    closing_prices['% Deviation'] = closing_prices['% Deviation'].round(2)
    data_close_sorted = closing_prices.sort_values(by='% Deviation', ascending=False)
    
    print("INFO: Saving 200wk_sma data to cloud cache...")
    cloud_storage.save_to_cache(data_close_sorted, cache_file)
    
    return data_close_sorted

def merge_stock_data(closing_prices: pd.DataFrame, moving_averages: pd.DataFrame) -> pd.DataFrame:
    """
    Combines the closing prices with the 200-week simple moving averages and their deviations.
    
    Args:
        closing_prices: DataFrame containing the closing prices of stocks.
        moving_averages: DataFrame containing the 200-week simple moving averages and their percentage deviations.
        
    Returns:
        A DataFrame that merges the two inputs, sorted by the percentage deviation from the moving average.
    """
    # Reset indices to ensure proper merging
    closing_prices = closing_prices.reset_index()
    moving_averages = moving_averages.reset_index()

    # Merge the dataframes on the ticker column
    merged_df = pd.merge(
        closing_prices,
        moving_averages[['Ticker', '200wk_sma', '% Deviation']],
        left_on='Ticker',
        right_on='Ticker'
    )

    merged_df.columns = merged_df.columns.astype(str)
    merged_df.drop(columns=["index", "Date"], inplace=True)
    merged_df.rename(columns={"200wk_sma": "200 Week SMA", "Security": "Company"}, inplace=True)
    new_order = ['% Deviation', 'Ticker', 'Company', '200 Week SMA', 'Close', 'Sector', 'Industry']
    merged_df = merged_df[new_order]
    # new_order = [6, 0, 2, 5, 1, 3, 4]  # The new column order by index
    # df = df.iloc[:, new_order]
    merged_df = merged_df.sort_values(by='% Deviation', ascending=True)

    # Save merged data to cache
    cache_file = 'final_merged_data_cache.pkl'
    cloud_storage.save_to_cache(merged_df, cache_file)

    return merged_df.sort_values('% Deviation')

def main():
    """
    Main function to fetch the stock data and print the closing prices.
    """
    closing_prices = fetch_stock_data()
    moving_averages = fetch_200_wk_simple_moving_average_SMA()
    merged_df = merge_stock_data(closing_prices, moving_averages)
    print(merged_df)


if __name__ == "__main__":
    main()
