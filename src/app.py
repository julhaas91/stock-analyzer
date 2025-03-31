"""
This module contains the Streamlit app for the stock analyzer.
"""

import streamlit as st
import pandas as pd
from main import fetch_stock_data, fetch_200_wk_simple_moving_average_SMA, merge_stock_data
from utils import load_or_download_sp500_tickers
from PIL import Image
import time
import plotly.express as px

st.set_page_config(page_title="Stock Analyzer", layout="wide")

# Initialize session state for login
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "sp500_stocks" not in st.session_state:
    st.session_state.sp500_stocks = None
if "data_fetched" not in st.session_state:
    st.session_state.data_fetched = False
if "merged_df" not in st.session_state:
    st.session_state.merged_df = None
if "lower_bound" not in st.session_state:
    st.session_state.lower_bound = None
if "upper_bound" not in st.session_state:
    st.session_state.upper_bound = None
if "filtered_df" not in st.session_state:
    st.session_state.filtered_df = None

# Login section
if not st.session_state.logged_in:
    st.title("Login")
    login_code = st.text_input("Please enter the access code:", type="password")
    
    if st.button("Login"):
        if login_code == "20255":  # Replace with your desired access code
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Wrong access code. Please try again.")
else:
    # Display header image
    header_image = Image.open("header.png")
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.image(header_image, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.title("S&P 500 Stock Analysis")

    # Add logout button
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.data_fetched = False
        st.rerun()

    # Automatically fetch S&P 500 stocks if not already done
    if st.session_state.sp500_stocks is None:
        with st.spinner("Fetching all S&P 500 stocks..."):
            st.session_state.sp500_stocks = load_or_download_sp500_tickers()
            progress_bar = st.progress(0)
            for i in range(100):
                progress_bar.progress(i + 1)
                time.sleep(0.01)

    if not st.session_state.sp500_stocks.empty:
        st.success(f"Number of stocks in S&P 500: {len(st.session_state.sp500_stocks)}")

    # Automatically fetch and display data if not already done
    if not st.session_state.data_fetched:
        with st.spinner("Downloading data..."):
            try:
                # Create a progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(current, total):
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"Loading Data: {current}/{total} Stocks")

                # Fetch the stock data (closing prices)
                closing_prices = fetch_stock_data()
                status_text.text("Data downloaded!")

                # Fetch the 200-week moving average data
                moving_averages = fetch_200_wk_simple_moving_average_SMA()
                status_text.text("200-Week SMA calculated!")
                
                # Merge the dataframes using the new function
                merged_df = merge_stock_data(closing_prices, moving_averages)
                
                # Store the merged dataframe in session state
                st.session_state.merged_df = merged_df
                
                # Initialize bounds if not set
                if st.session_state.lower_bound is None:
                    st.session_state.lower_bound = float(merged_df['% Deviation'].min())
                if st.session_state.upper_bound is None:
                    st.session_state.upper_bound = float(merged_df['% Deviation'].max())
                if st.session_state.filtered_df is None:
                    st.session_state.filtered_df = merged_df

                st.session_state.data_fetched = True

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

    # Display filter UI and filtered data if we have data
    if st.session_state.merged_df is not None:
        # Add threshold filters
        st.subheader("Setting the Boundaries above and below the 200-Week SMA")
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            new_lower_bound = st.slider(
                "Lower Bound (%)",
                min_value=float(st.session_state.merged_df['% Deviation'].min()),
                max_value=float(st.session_state.merged_df['% Deviation'].max()),
                value=st.session_state.lower_bound,
                step=0.1
            )
        
        with col2:
            new_upper_bound = st.slider(
                "Upper Bound (%)",
                min_value=float(st.session_state.merged_df['% Deviation'].min()),
                max_value=float(st.session_state.merged_df['% Deviation'].max()),
                value=st.session_state.upper_bound,
                step=0.1
            )

        with col3:
            st.write("")  # Add some spacing
            if st.button("Update"):
                st.session_state.lower_bound = new_lower_bound
                st.session_state.upper_bound = new_upper_bound
                st.session_state.filtered_df = st.session_state.merged_df[
                    (st.session_state.merged_df['% Deviation'] >= st.session_state.lower_bound) & 
                    (st.session_state.merged_df['% Deviation'] <= st.session_state.upper_bound)
                ]
                st.rerun()

        # Display the filtered dataframe
        st.subheader("Stock Prices with 200-Week SMA")
        st.dataframe(st.session_state.filtered_df)

        # Create bubble chart
        st.subheader("Visualization of Deviations")
        
        # Create a copy of filtered data for visualization
        viz_df = st.session_state.filtered_df.copy()
        viz_df['Abs_Deviation'] = viz_df['% Deviation'].abs()
        
        # Create bubble chart
        fig = px.scatter(
            viz_df,
            x='Ticker',
            y='% Deviation',
            size='Abs_Deviation',
            color='% Deviation',
            color_continuous_scale=['#ff9999', '#ffffff', '#99ff99'],  # Red to white to green
            color_continuous_midpoint=0,
            title='Bubble Chart of Deviations from 200-Week SMA',
            labels={
                'Ticker': 'Stock Symbol',
                '% Deviation': 'Deviation (%)',
                'Abs_Deviation': 'Absolute Deviation (%)'
            }
        )
        
        # Update layout for better readability
        fig.update_layout(
            xaxis_tickangle=-45,
            showlegend=False,
            height=600,
            margin=dict(t=50, b=100)
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        
        with col1:
            above_threshold = st.number_input(
                "SET Above-Theshold (%)",
                min_value=0.0,
                max_value=float(st.session_state.merged_df['% Deviation'].max()),
                value=50.0,
                step=1.0
            )
            
            above_threshold_df = viz_df[viz_df['% Deviation'] > above_threshold].copy()
            if not above_threshold_df.empty:
                fig_above_threshold = px.scatter(
                    above_threshold_df,
                    x='Ticker',
                    y='% Deviation',
                    size='Abs_Deviation',
                    color='% Deviation',
                    color_continuous_scale=['#ff9999', '#ff0000'],  # Light red to dark red
                    title=f'ABOVE-THRESHOLD (above {above_threshold}% ABOVE 200-SMA)',
                    labels={
                        'Ticker': 'Stock Symbol',
                        '% Deviation': 'Deviation (%)',
                        'Abs_Deviation': 'Absolute Deviation (%)'
                    }
                )
                fig_above_threshold.update_layout(
                    xaxis_tickangle=-45,
                    showlegend=False,
                    height=400,
                    margin=dict(t=50, b=100)
                )
                st.plotly_chart(fig_above_threshold, use_container_width=True)
            else:
                st.info(f"No stocks found above {above_threshold}% above 200-SMA")

        with col2:
            below_threshold = st.number_input(
                "SET Below-Threshold (%)",
                min_value=float(st.session_state.merged_df['% Deviation'].min()),
                max_value=0.0,
                value=-30.0,
                step=1.0
            )
            
            below_threshold_df = viz_df[viz_df['% Deviation'] < below_threshold].copy()
            if not below_threshold_df.empty:
                fig_below_threshold = px.scatter(
                    below_threshold_df,
                    x='Ticker',
                    y='% Deviation',
                    size='Abs_Deviation',
                    color='% Deviation',
                    color_continuous_scale=['#99ff99', '#00ff00'],  # Light green to dark green
                    title=f'BELOW-THRESHOLD ({below_threshold}% BELOW 200-SMA)',
                    labels={
                        'Ticker': 'Stock Symbol',
                        '% Deviation': 'Deviation (%)',
                        'Abs_Deviation': 'Absolute Deviation (%)'
                    }
                )
                fig_below_threshold.update_layout(
                    xaxis_tickangle=-45,
                    showlegend=False,
                    height=400,
                    margin=dict(t=50, b=100)
                )
                st.plotly_chart(fig_below_threshold, use_container_width=True)
            else:
                st.info(f"No stocks found below {below_threshold}% below 200-SMA")

        # Add download button for filtered CSV
        csv_filtered = st.session_state.filtered_df.to_csv(index=False)
        st.download_button(
            label="Filtered Data as CSV Download",
            data=csv_filtered,
            file_name="sp500_filtered.csv",
            mime="text/csv"
        )

        # Add footer links
        st.markdown("---")
        st.markdown("""
            <style>
            .icon-button {
                display: inline-block;
                padding: 10px 20px;
                background-color: #f0f2f6;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                transition: background-color 0.3s;
                margin: 0 5px;
            }
            .icon-button:hover {
                background-color: #e0e2e6;
            }
            .button-container {
                text-align: center;
            }
            </style>
            <div class="button-container">
                <a href="https://julhaas.me" target="_blank" class="icon-button">
                    🌐 juliushaas.me
                </a>
                <a href="mailto:juliushaas91@gmail.com" class="icon-button">
                    ✉️ Email
                </a>
                <a href="https://linkedin.com/in/jh91" target="_blank" class="icon-button">
                    👥 LinkedIn
                </a>
                <a href="https://github.com/julhaas91/stock-analyzer" target="_blank" class="icon-button">
                    💻 Source Code (GitHub)
                </a>
            </div>
        """, unsafe_allow_html=True)
