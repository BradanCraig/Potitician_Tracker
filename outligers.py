from sklearn.neighbors import LocalOutlierFactor
import numpy as np
import pandas as pd
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries

api_key = ""

def analyze(ticker_symbol, origional_price):
    try:
        ticker = yf.Ticker(ticker=ticker_symbol)
        hist = ticker.history(period="1d")  # last trading day
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
        print(f"\nTicker {ticker_symbol}\nCurrent Price: {current_price}\nOriginal Price: {origional_price}\nDifference: {current_price - origional_price}\nPercent difference{((current_price - origional_price) / origional_price) * 100}")
        return ((current_price - origional_price) / origional_price) * 100
    except:
        return None
        # ts = TimeSeries(key=api_key, output_format='pandas')

        # # Using the Global Quote endpoint (latest price)
        # data, meta_data = ts.get_quote_endpoint(symbol=ticker)

        # '05. price' gives the latest price
        # current_price = float(data['05. price'][0])        
        # return ((current_price - origional_price) / origional_price) * 100

def main():
    df = pd.read_csv("input_data_full.csv")
    input_data_df = df[["base_amount", "PE Ratio", "ROE", "Profit Margin", "TTM Revenue", "price_at_trade"]]
    input_data_df.to_csv("almost.csv",index=False)
    input_data_df = input_data_df.fillna(-9999999)
    input_data = input_data_df.values

    lof = LocalOutlierFactor(n_neighbors=20, contamination=0.1)
    y_pred = lof.fit_predict(input_data)
    outlier_scores = lof.negative_outlier_factor_

    outliers = input_data_df.index[y_pred == -1].to_list()
    inliers = input_data_df[y_pred == 1]

    outlier_tickers = df.loc[outliers, ['ticker', 'price_at_trade']]
    print(outlier_tickers)
    
    differences = []
    for _, row in outlier_tickers.iterrows():
        result = analyze(ticker_symbol=row[0], origional_price=row[1])
        if result is None:
            continue

        differences.append(result)

    print(differences)
    print(f"Percent difference is {sum(differences)/len(differences)}")

main()