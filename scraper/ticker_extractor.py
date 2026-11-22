import pandas as pd
import re
import yfinance as yf
from tqdm import tqdm
from typing import TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from data_collector import TickerScraper


class TickerExtractor:
    def __init__(self, data_frame_path: Path):
        self.scraped_dataframe = pd.read_csv(data_frame_path)
        self.purchased_trades_dataframe = pd.DataFrame()

    @staticmethod
    def extract_lower_purchase_amount(value):
        # Extract first number in string
        numbers = re.findall(r"\d+", value.replace(",", ""))
        if numbers:
            return int(numbers[0])
        return None

    def parse_income_stmt(self, q_statement_df):
        if q_statement_df.empty:
            return pd.Series()

        # Take the last available quarter (yfinance returns columns as dates)
        latest_quarter = q_statement_df.columns[-1]
        col_data = q_statement_df[latest_quarter]

        # TODO: check this
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

    def get_stock_info(self, ticker_symbol, date):
        ticker = yf.Ticker(ticker_symbol)

        # Historical price at the date
        hist = ticker.history(
            start=date, end=pd.to_datetime(date) + pd.Timedelta(days=1)
        )
        if hist.empty:
            price_at_trade = None
        else:
            price_at_trade = hist["Close"].iloc[0]

        # Quarterly income statement
        q_income = ticker.quarterly_income_stmt
        parsed_income = self.parse_income_stmt(q_income)

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
            "quarterly_income": parsed_income,
        }

    def get_ticker_info(self):
        # Filter only purchases
        purchase_rows = self.scraped_dataframe[
            self.scraped_dataframe["type"] == "Purchase"
        ].copy()
        # Get lowest amount
        purchase_rows["base_amount"] = purchase_rows["amount"].apply(
            self.extract_lower_purchase_amount
        )
        self.purchased_trades_dataframe = purchase_rows.drop(
            columns=["amount", "name"], errors="ignore"
        )

        for i, trade in purchase_rows.iterrows():
            self.extract_lower_purchase_amount(trade)
            date_str = trade.iloc[0]
            ticker_symbol = trade.iloc[1]

            date = pd.to_datetime(date_str, errors="coerce")

            # Return early if no date is given
            if pd.isna(date):
                continue

            stock_data = self.get_stock_info(ticker_symbol=ticker_symbol, date=date)

            # TODO: might be able to delete as this is just for statistics tracking
            if stock_data["price_at_trade"] is None:
                print(f"No purchase price available for {ticker_symbol}, skipping")
                continue

            merged_row = trade.to_dict()
            merged_row.update(stock_data["key_metrics"])
            merged_row.update(stock_data["quarterly_income"].to_dict())
            merged_row["price_at_trade"] = stock_data["price_at_trade"]

            self.purchased_trades_dataframe = pd.concat(
                [self.purchased_trades_dataframe, pd.DataFrame([merged_row])],
                ignore_index=True,
            )

        self.purchased_trades_dataframe.to_csv("input_data_full.csv", index=False)
