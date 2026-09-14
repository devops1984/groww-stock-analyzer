import streamlit as st
import pandas as pd
import yfinance as yf
from prophet import Prophet

from stock_forecast import TOP_20_BY_CATEGORY, TICKER_MAP, normalize_stock_name

st.title("📊 Groww Portfolio Analyzer")

portfolio = pd.read_csv("groww_portfolio.csv")
st.write("### Your Portfolio", portfolio)

portfolio_stocks = portfolio.get("Stock", pd.Series(dtype=str)).dropna().astype(str).str.strip()
portfolio_stocks = portfolio_stocks[portfolio_stocks != ""].tolist()
category = st.selectbox("Category", ["Portfolio", *TOP_20_BY_CATEGORY.keys()])

if category == "Portfolio" and portfolio_stocks:
    available_stocks = portfolio_stocks
elif category == "Portfolio":
    available_stocks = [name for stocks in TOP_20_BY_CATEGORY.values() for name, _ in stocks]
else:
    available_stocks = [name for name, _ in TOP_20_BY_CATEGORY[category]]

selected_stock = st.selectbox("Choose a stock to forecast", available_stocks)

if st.button("Run Forecast"):
    ticker = TICKER_MAP.get(normalize_stock_name(selected_stock))
    if not ticker:
        st.error(f"No ticker mapping found for {selected_stock}.")
        st.stop()

    data = yf.download(ticker, start="2020-01-01", auto_adjust=False)
    if data.empty or "Close" not in data:
        st.error(f"No price data was returned for {ticker}.")
        st.stop()

    close_prices = data["Close"]
    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.iloc[:, 0]

    df = pd.DataFrame({
        "ds": pd.to_datetime(data.index),
        "y": pd.to_numeric(close_prices, errors="coerce")
    }).dropna()

    if len(df) < 2:
        st.error(f"Not enough valid price data was returned for {ticker}.")
        st.stop()

    model = Prophet(daily_seasonality=True)
    model.fit(df)

    future = model.make_future_dataframe(periods=180)
    forecast = model.predict(future)

    st.line_chart(forecast[['ds','yhat']].set_index('ds'))
