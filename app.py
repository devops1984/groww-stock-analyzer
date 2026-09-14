import streamlit as st
import pandas as pd
import yfinance as yf
from prophet import Prophet

from stock_forecast import TOP_20_BY_CATEGORY, TICKER_MAP, normalize_stock_name

st.set_page_config(page_title="Groww Investment Research", layout="wide")
st.title("Groww Investment Research")
st.caption("Quantitative research signals from market data. This is not personalized financial advice.")

portfolio = pd.read_csv("groww_portfolio.csv")
portfolio_stocks = portfolio.get("Stock", pd.Series(dtype=str)).dropna().astype(str).str.strip()
portfolio_stocks = portfolio_stocks[portfolio_stocks != ""].tolist()
category = st.selectbox("Category", ["Portfolio", *TOP_20_BY_CATEGORY.keys()])

if category == "Portfolio" and portfolio_stocks:
    available_stocks = portfolio_stocks
elif category == "Portfolio":
    available_stocks = [name for stocks in TOP_20_BY_CATEGORY.values() for name, _ in stocks]
else:
    available_stocks = [name for name, _ in TOP_20_BY_CATEGORY[category]]



def ticker_for(stock_name):
    return TICKER_MAP.get(normalize_stock_name(stock_name))


@st.cache_data(ttl=3600, show_spinner=False)
def load_history(ticker):
    data = yf.download(ticker, period="5y", auto_adjust=False, progress=False)
    if data.empty or "Close" not in data:
        return pd.DataFrame(columns=["ds", "close"])

    close_prices = data["Close"]
    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.iloc[:, 0]

    return pd.DataFrame({
        "ds": pd.to_datetime(data.index),
        "close": pd.to_numeric(close_prices, errors="coerce")
    }).dropna()


def calculate_metrics(stock_name):
    ticker = ticker_for(stock_name)
    if not ticker:
        return None

    history = load_history(ticker)
    if len(history) < 60:
        return None

    prices = history.set_index("ds")["close"]
    daily_returns = prices.pct_change().dropna()
    one_year = prices.tail(252)
    one_year_return = (one_year.iloc[-1] / one_year.iloc[0] - 1) * 100
    six_month_return = (prices.iloc[-1] / prices.iloc[-min(126, len(prices))] - 1) * 100
    one_month_return = (prices.iloc[-1] / prices.iloc[-min(22, len(prices))] - 1) * 100
    volatility = daily_returns.tail(252).std() * (252 ** 0.5) * 100
    drawdown = prices / prices.cummax() - 1
    max_drawdown = drawdown.tail(252).min() * 100
    sma_50 = prices.tail(50).mean()
    sma_200 = prices.tail(min(200, len(prices))).mean()
    trend = "Positive" if prices.iloc[-1] > sma_50 > sma_200 else "Negative" if prices.iloc[-1] < sma_50 < sma_200 else "Mixed"

    score = (
        max(-20, min(20, one_year_return / 4))
        + max(-15, min(15, six_month_return / 3))
        + (10 if trend == "Positive" else -10 if trend == "Negative" else 0)
        - max(0, min(15, volatility / 4))
        + max(-10, min(10, max_drawdown / 4))
    )
    signal = "Research priority" if score >= 8 else "Monitor" if score >= -5 else "Review risk"

    return {
        "Stock": stock_name,
        "Ticker": ticker,
        "Current price": prices.iloc[-1],
        "1M return %": one_month_return,
        "6M return %": six_month_return,
        "1Y return %": one_year_return,
        "Volatility %": volatility,
        "Max drawdown %": max_drawdown,
        "Trend": trend,
        "Score": score,
        "Signal": signal,
    }


st.subheader("Market-based comparison")
st.caption("Score combines recent returns, trend, volatility, and drawdown. It is a screening aid, not a recommendation.")
with st.spinner("Downloading recent market data..."):
    analysis_rows = [calculate_metrics(stock) for stock in available_stocks]
analysis = pd.DataFrame([row for row in analysis_rows if row is not None])

if analysis.empty:
    st.error("No usable market data was returned for this selection.")
    st.stop()

display_columns = ["Stock", "Current price", "1M return %", "6M return %", "1Y return %", "Volatility %", "Max drawdown %", "Trend", "Score", "Signal"]
st.dataframe(
    analysis[display_columns].sort_values("Score", ascending=False).style.format({
        "Current price": "{:.2f}", "1M return %": "{:.1f}", "6M return %": "{:.1f}",
        "1Y return %": "{:.1f}", "Volatility %": "{:.1f}", "Max drawdown %": "{:.1f}", "Score": "{:.1f}"
    }),
    use_container_width=True,
    hide_index=True,
)

st.subheader("Portfolio data quality")
if "Quantity" not in portfolio or portfolio["Quantity"].fillna("").astype(str).str.strip().eq("").all():
    st.warning("Groww did not provide quantities in groww_portfolio.csv. Allocation, invested value, and portfolio profit/loss cannot be calculated until quantities are available.")
else:
    st.success("Quantities are available; allocation analysis can be added from those holdings.")

selected_stock = st.selectbox("Choose a stock to forecast", available_stocks)

if st.button("Run Forecast"):
    ticker = ticker_for(selected_stock)
    if not ticker:
        st.error(f"No ticker mapping found for {selected_stock}.")
        st.stop()

    data = yf.download(ticker, start="2020-01-01", auto_adjust=False, progress=False)
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

    st.line_chart(forecast[["ds", "yhat"]].set_index("ds"))

    selected_metrics = analysis[analysis["Stock"] == selected_stock].iloc[0]
    st.write(f"**Screening signal:** {selected_metrics['Signal']} | **Score:** {selected_metrics['Score']:.1f} / 50")
    st.caption("Forecasts are model estimates with substantial uncertainty. Validate company fundamentals, valuation, liquidity, taxes, and your own risk tolerance before investing.")
