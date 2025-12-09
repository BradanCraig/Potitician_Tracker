import pandas as pd
import re
import yfinance as yf
from tqdm import tqdm

def extract_lower(value):
    # Extract first number in string
    numbers = re.findall(r'\d+', value.replace(',', ''))
    if numbers:
        return int(numbers[0])
    return None

# --- Function to parse quarterly income statement into columns ---
def parse_income_stmt(stmt_df):
    if stmt_df.empty:
        return pd.Series()
    
    # Take the last available quarter (yfinance returns columns as dates)
    latest_quarter = stmt_df.columns[-1]
    col_data = stmt_df[latest_quarter]
    
    # Convert to string -> parse metric/value pairs
    if isinstance(col_data, pd.Series):
        return col_data  # Already Series, index is metric
    else:
        # Fallback: sometimes col_data is string
        result = {}
        for line in str(col_data).split("\n"):
            if line.strip() == "":
                continue
            *metric_parts, value_str = line.rsplit(maxsplit=1)
            metric = " ".join(metric_parts).strip()
            try:
                value = float(value_str)
            except ValueError:
                value = value_str
            result[metric] = value
        return pd.Series(result)

# --- Function to get stock info at a specific date ---
def get_stock_info(ticker_symbol, date):
    ticker = yf.Ticker(ticker_symbol)
    
    # Historical price at the date
    hist = ticker.history(start=date, end=pd.to_datetime(date) + pd.Timedelta(days=1))
    if hist.empty:
        price_at_trade = None
    else:
        price_at_trade = hist['Close'].iloc[0]
    
    # Quarterly income statement
    q_income = ticker.quarterly_income_stmt
    parsed_income = parse_income_stmt(q_income)
    
    # Key metrics (info dict)
    info = ticker.info
    key_metrics = {
        "PE Ratio": info.get("trailingPE"),
        "ROE": info.get("returnOnEquity"),
        "Profit Margin": info.get("profitMargins"),
        "TTM Revenue": info.get("totalRevenue"),
    }
    
    return {
        "price_at_trade": price_at_trade,
        "key_metrics": key_metrics,
        "quarterly_income": parsed_income
    }

# --- Main function ---
def get_ticker_info():
    df = pd.read_csv("usable_data.csv")
    
    # Filter only purchases
    purchase_rows = df[df["type"] == "Purchase"].copy()
    purchase_rows["base_amount"] = purchase_rows["amount"].apply(extract_lower)
    purchase_rows = purchase_rows.drop(columns=["amount", "name"], errors='ignore')
    
    results_list = []
    
    for _, row in tqdm(purchase_rows.iterrows(), total=len(purchase_rows)):
        date_str = row.iloc[0]
        ticker_symbol = row.iloc[1]

        
        date = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(date):
            continue
        
        stock_data = get_stock_info(ticker_symbol=ticker_symbol, date=date)
        if stock_data["price_at_trade"] is None:
            print("continuing")
            continue
        # Merge row with quarterly income statement and key metrics
        merged_row = row.to_dict()
        merged_row.update(stock_data["key_metrics"])
        merged_row.update(stock_data["quarterly_income"].to_dict())
        merged_row["price_at_trade"] = stock_data["price_at_trade"]
        
        results_list.append(merged_row)
        final_df = pd.DataFrame(results_list)
        final_df.to_csv("input_data_full.csv", index=False)

    # Convert to dataframe
    print("Saved enriched data to input_data.csv")

# Run

get_ticker_info()
