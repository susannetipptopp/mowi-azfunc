import yfinance as yf
import datetime

TICKER = "MOWI.OL"

def get_mowi_data():
    """
    Fetches real‐time quote data for MOWI.OL.
    """
    t = yf.Ticker(TICKER)
    info = t.info
    return {
        "symbol": info.get("symbol"),
        "last_price": info.get("regularMarketPrice"),
        "previous_close": info.get("previousClose"),
        "open": info.get("open"),
        "day_high": info.get("dayHigh"),
        "day_low": info.get("dayLow"),
        "volume": info.get("volume"),
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency"),
    }

def get_mowi_history(days=30, interval="1d"):
    """
    Returns a DataFrame of the last `days` days of historical data,
    at the given interval (e.g. "1d", "1wk", "1mo").
    """
    end = datetime.date.today()
    start = end - datetime.timedelta(days=days)
    return yf.Ticker(TICKER).history(start=start, end=end, interval=interval)

def get_mowi_actions():
    """
    Returns a DataFrame with dividends and stock splits.
    """
    return yf.Ticker(TICKER).actions

def get_mowi_financials():
    """
    Returns dicts of major financial statements:
    - income_statement
    - balance_sheet
    - cashflow
    """
    t = yf.Ticker(TICKER)
    return {
        "income_statement": t.financials,
        "balance_sheet": t.balance_sheet,
        "cashflow": t.cashflow,
    }

def get_mowi_recommendations():
    """
    Returns the analyst recommendation trends.
    """
    return yf.Ticker(TICKER).recommendations

if __name__ == "__main__":
    print("=== Real-time quote ===")
    print(get_mowi_data(), end="\n\n")

    print("=== Last 30 days history ===")
    hist = get_mowi_history(30)
    print(hist.tail(), end="\n\n")    # show just the last few rows

    print("=== Dividends & Splits ===")
    print(get_mowi_actions(), end="\n\n")

    print("=== Financial Statements ===")
    fin = get_mowi_financials()
    print("Income Statement:\n", fin["income_statement"].head(), end="\n\n")
    print("Balance Sheet:\n", fin["balance_sheet"].head(), end="\n\n")
    print("Cash Flow:\n", fin["cashflow"].head(), end="\n\n")

    print("=== Analyst Recommendations ===")
    rec = get_mowi_recommendations()
    print(rec.tail())
