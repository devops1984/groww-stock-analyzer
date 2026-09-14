try:
    import yfinance as yf  # type: ignore[import-not-found]
except ImportError:
    yf = None

try:
    import pandas as pd  # type: ignore[import-not-found]
except ImportError:
    raise SystemExit("pandas is required to run this script. Please install it with 'pip install pandas'.")

try:
    from prophet import Prophet  # type: ignore[import-not-found]
except ImportError:
    Prophet = None

try:
    import matplotlib  # type: ignore[import-not-found, reportMissingModuleSource]
    matplotlib.use("Agg")  # use non-GUI backend for plotting

    import matplotlib.pyplot as plt  # type: ignore[import-not-found]
except ImportError:
    plt = None

# Default Groww universe. The first 20 symbols in every category are used when
# no portfolio rows are available.
TOP_20_BY_CATEGORY = {
    "Banking": [
        ("HDFC Bank", "HDFCBANK.NS"), ("ICICI Bank", "ICICIBANK.NS"),
        ("State Bank Of India", "SBIN.NS"), ("Axis Bank", "AXISBANK.NS"),
        ("Kotak Mahindra Bank", "KOTAKBANK.NS"), ("Indusind Bank", "INDUSINDBK.NS"),
        ("Bank Of Baroda", "BANKBARODA.NS"), ("Punjab National Bank", "PNB.NS"),
        ("Canara Bank", "CANBK.NS"), ("Union Bank Of India", "UNIONBANK.NS"),
        ("IDBI Bank", "IDBI.NS"), ("Federal Bank", "FEDERALBNK.NS"),
        ("Bank Of India", "BANKINDIA.NS"), ("Indian Bank", "INDIANB.NS"),
        ("Yes Bank", "YESBANK.NS"), ("AU Small Finance Bank", "AUBANK.NS"),
        ("Bandhan Bank", "BANDHANBNK.NS"), ("RBL Bank", "RBLBANK.NS"),
        ("IDFC First Bank", "IDFCFIRSTB.NS"), ("Karur Vysya Bank", "KARURVYSYA.NS")
    ],
    "IT": [
        ("TCS", "TCS.NS"), ("Infosys", "INFY.NS"), ("HCL Tech", "HCLTECH.NS"),
        ("Wipro", "WIPRO.NS"), ("Tech Mahindra", "TECHM.NS"), ("LTIMindtree", "LTIM.NS"),
        ("Persistent Systems", "PERSISTENT.NS"), ("Mphasis", "MPHASIS.NS"),
        ("Coforge", "COFORGE.NS"), ("Oracle Financial Services", "OFSS.NS"),
        ("Tata Elxsi", "TATAELXSI.NS"), ("KPIT Technologies", "KPITTECH.NS"),
        ("Cyient", "CYIENT.NS"), ("Birlasoft", "BSOFT.NS"),
        ("Sonata Software", "SONATSOFTW.NS"), ("Happiest Minds", "HAPPSTMNDS.NS"),
        ("Route Mobile", "ROUTE.NS"), ("Tanla Platforms", "TANLA.NS"),
        ("Intellect Design Arena", "INTELLECT.NS"), ("Mastek", "MASTEK.NS")
    ],
    "Pharma": [
        ("Sun Pharma", "SUNPHARMA.NS"), ("Dr Reddy's Labs", "DRREDDY.NS"),
        ("Cipla", "CIPLA.NS"), ("Divis Labs", "DIVISLAB.NS"), ("Biocon", "BIOCON.NS"),
        ("Apollo Hospitals", "APOLLOHOSP.NS"), ("Lupin", "LUPIN.NS"),
        ("Aurobindo Pharma", "AUROPHARMA.NS"), ("Torrent Pharma", "TORNTPHARM.NS"),
        ("Zydus Lifesciences", "ZYDUSLIFE.NS"), ("Alkem Laboratories", "ALKEM.NS"),
        ("Max Healthcare", "MAXHEALTH.NS"), ("Abbott India", "ABBOTINDIA.NS"),
        ("Glenmark Pharma", "GLENMARK.NS"), ("Ipca Laboratories", "IPCALAB.NS"),
        ("Jubilant Pharmova", "JUBLINGREA.NS"), ("Natco Pharma", "NATCOPHARM.NS"),
        ("Syngene International", "SYNGENE.NS"), ("Piramal Pharma", "PPLPHARMA.NS"),
        ("Laurus Labs", "LAURUSLABS.NS")
    ],
    "FMCG": [
        ("Hindustan Unilever", "HINDUNILVR.NS"), ("ITC", "ITC.NS"),
        ("Nestle India", "NESTLEIND.NS"), ("Britannia", "BRITANNIA.NS"),
        ("Varun Beverages", "VBL.NS"), ("Dabur", "DABUR.NS"),
        ("Tata Consumer Products", "TATACONSUM.NS"), ("Godrej Consumer Products", "GODREJCP.NS"),
        ("Marico", "MARICO.NS"), ("Colgate Palmolive", "COLPAL.NS"),
        ("United Spirits", "UNITDSPR.NS"), ("Jubilant Foodworks", "JUBLFOOD.NS"),
        ("Procter & Gamble Hygiene", "PGHH.NS"), ("Emami", "EMAMILTD.NS"),
        ("United Breweries", "UBL.NS"), ("Radico Khaitan", "RADICO.NS"),
        ("Honasa Consumer", "HONASA.NS"), ("Zydus Wellness", "ZYDUSWELL.NS"),
        ("Tata Coffee", "TATACOFFEE.NS"), ("CCL Products", "CCL.NS")
    ],
    "Auto": [
        ("Maruti Suzuki", "MARUTI.NS"), ("Tata Motors", "TATAMOTORS.NS"),
        ("Mahindra & Mahindra", "M&M.NS"), ("Bajaj Auto", "BAJAJ-AUTO.NS"),
        ("Eicher Motors", "EICHERMOT.NS"), ("Hero MotoCorp", "HEROMOTOCO.NS"),
        ("TVS Motor", "TVSMOTOR.NS"), ("Ashok Leyland", "ASHOKLEY.NS"),
        ("Samvardhana Motherson", "MOTHERSON.NS"), ("Bosch", "BOSCHLTD.NS"),
        ("Bharat Forge", "BHARATFORG.NS"), ("Balkrishna Industries", "BALKRISIND.NS"),
        ("Tube Investments", "TIINDIA.NS"), ("Exide Industries", "EXIDEIND.NS"),
        ("Motherson Sumi Wiring", "MSUMI.NS"), ("Sona BLW Precision", "SONACOMS.NS"),
        ("Endurance Technologies", "ENDURANCE.NS"), ("Cummins India", "CUMMINSIND.NS"),
        ("Craftsman Automation", "CRAFTSMAN.NS"), ("Olectra Greentech", "OLECTRA.NS")
    ]
}

# Personalized aliases retained for existing Groww portfolio names.
TICKER_MAP = {
    # Banks & Financials
    "Hdfc Bank": "HDFCBANK.NS",
    "Icici Bank": "ICICIBANK.NS",
    "Axis Bank": "AXISBANK.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS",
    "State Bank Of India": "SBIN.NS",
    "Indusind Bank": "INDUSINDBK.NS",

    # Pharma & Healthcare
    "Dr Reddy'S Labs": "DRREDDY.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "Cipla": "CIPLA.NS",
    "Divis Labs": "DIVISLAB.NS",
    "Biocon": "BIOCON.NS",

    # IT & Tech
    "Infosys": "INFY.NS",
    "Tcs": "TCS.NS",
    "Wipro": "WIPRO.NS",
    "Tech Mahindra": "TECHM.NS",
    "Hcl Tech": "HCLTECH.NS",
    "Persistent Systems": "PERSISTENT.NS",
    "Mindtree": "LTIM.NS",           # merged into LTI Mindtree

    # FMCG & Beverages
    "Varun Beverages": "VBL.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "Nestle India": "NESTLEIND.NS",
    "Britannia": "BRITANNIA.NS",
    "Dabur": "DABUR.NS",

    # Industrials & Auto
    "Samvardhana Motherson": "MOTHERSON.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Mahindra & Mahindra": "M&M.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Bajaj Auto": "BAJAJ-AUTO.NS",
    "Ashok Leyland": "ASHOKLEY.NS",

    # Holdings & Diversified
    "Bajaj Hold & Invest": "BAJAJHLDNG.NS",
    "Reliance Industries": "RELIANCE.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Adani Green": "ADANIGREEN.NS",
    "Adani Ports": "ADANIPORTS.NS",
    "Adani Power": "ADANIPOWER.NS"
}

for category_stocks in TOP_20_BY_CATEGORY.values():
    TICKER_MAP.update(category_stocks)


def normalize_stock_name(value):
    return " ".join(str(value).replace(".", "").replace(",", "").split()).title()

def forecast_stock(ticker):
    try:
        data = yf.download(ticker, start="2020-01-01")

        if data.empty or len(data) < 2:
            print(f"⚠️ Not enough data for {ticker}, saving placeholder chart...")
            plt.figure()
            plt.text(0.5, 0.5, f"Not enough data for {ticker}", ha='center', va='center')
            plt.savefig(f"{ticker}_forecast.png")
            plt.close()
            return

        # Proper dataframe for Prophet
        df = pd.DataFrame({
            'ds': pd.to_datetime(data.index),
            'y': data['Close'].to_numpy().ravel().astype(float)
        }).dropna()

        if df.shape[0] < 2:
            print(f"⚠️ Not enough valid rows for {ticker}, saving placeholder chart...")
            plt.figure()
            plt.text(0.5, 0.5, f"Not enough valid data for {ticker}", ha='center', va='center')
            plt.savefig(f"{ticker}_forecast.png")
            plt.close()
            return

        model = Prophet()
        model.fit(df)

        future = model.make_future_dataframe(periods=180)
        forecast = model.predict(future)

        fig = model.plot(forecast)
        plt.title(f"Forecast for {ticker}")

        filename = f"{ticker}_forecast.png"
        plt.savefig(filename)
        plt.close()
        print(f"✅ Saved forecast chart as {filename}")

    except Exception as e:
        print(f"❌ Error forecasting {ticker}: {e}")


def main():
    # Use the Groww portfolio when it has stock names; otherwise use the
    # default top-20 universe from each configured category.
    portfolio = pd.read_csv("groww_portfolio.csv")
    portfolio_stocks = portfolio.get("Stock", pd.Series(dtype=str)).dropna().astype(str).str.strip()
    portfolio_stocks = portfolio_stocks[portfolio_stocks != ""]
    stocks_to_forecast = portfolio_stocks.tolist()

    if not stocks_to_forecast:
        stocks_to_forecast = [
            name for category_stocks in TOP_20_BY_CATEGORY.values()
            for name, _ in category_stocks
        ]
        print("No Groww portfolio stocks found; using the default top 20 from each category.")

    for stock in stocks_to_forecast:
        stock_clean = normalize_stock_name(stock)
        ticker = TICKER_MAP.get(stock_clean)

        if ticker:
            print(f"Forecasting {stock_clean} ({ticker})...")
            forecast_stock(ticker)
        else:
            print(f"No ticker mapping found for '{stock_clean}'")


if __name__ == "__main__":
    main()
