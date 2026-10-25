import time
import warnings
from datetime import datetime

import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore", message=".*inplace keyword.*")

TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "JPM", "KO", "XOM", "WMT"]
EMA_DAYS = 10
SMA_DAYS = 20
REFRESH_MINUTES = 30


def analyze(close: pd.Series):
    ema = close.ewm(span=EMA_DAYS, adjust=False).mean()
    sma = close.rolling(SMA_DAYS).mean()
    above = ema > sma

    if above.iloc[-1] and not above.iloc[-2]:
        signal = "BUY"
    elif not above.iloc[-1] and above.iloc[-2]:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "price": close.iloc[-1],
        "ema": ema.iloc[-1],
        "sma": sma.iloc[-1],
        "state": "EMA nad SMA" if above.iloc[-1] else "EMA pod SMA",
        "signal": signal,
    }


def run_once(last_signals: dict):
    data = yf.download(TICKERS, period="1y", auto_adjust=True, progress=False)["Close"]
    counts = {"BUY": 0, "SELL": 0, "HOLD": 0}

    print(f"\n=== {datetime.now():%Y-%m-%d %H:%M:%S} ===")
    print(f"{'Spółka':<8}{'Cena':>10}{'EMA':>10}{'SMA':>10}  {'Stan':<14}Sygnał")
    for ticker in TICKERS:
        if ticker not in data.columns:
            print(f"{ticker:<8}brak danych")
            continue
        close = data[ticker].dropna()
        if len(close) <= SMA_DAYS:
            print(f"{ticker:<8}za mało danych")
            continue
        r = analyze(close)
        counts[r["signal"]] += 1
        changed = ""
        if ticker in last_signals and last_signals[ticker] != r["signal"]:
            changed = "  <- zmiana od ostatniego odświeżenia"
        last_signals[ticker] = r["signal"]
        print(
            f"{ticker:<8}{r['price']:>10.2f}{r['ema']:>10.2f}{r['sma']:>10.2f}"
            f"  {r['state']:<14}{r['signal']}{changed}"
        )

    print(f"BUY: {counts['BUY']}  SELL: {counts['SELL']}  HOLD: {counts['HOLD']}")


def main():
    last_signals = {}
    try:
        while True:
            try:
                run_once(last_signals)
            except Exception as e:
                print(f"Błąd pobierania danych: {e}")
            print(f"Następne odświeżenie za {REFRESH_MINUTES} min (Stop w PyCharmie, żeby przerwać).")
            time.sleep(REFRESH_MINUTES * 60)
    except KeyboardInterrupt:
        print("\nZatrzymano.")


if __name__ == "__main__":
    main()