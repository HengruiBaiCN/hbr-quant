import akshare as ak
import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import schedule
import time

def init():
    """
    Initialize strategy settings
    """
    global max_holdings, max_days, stop_gain, stop_loss, portfolio, cash, initial_cash, history
    max_holdings = 10
    max_days = 15
    stop_gain = 0.2
    stop_loss = 0.05
    portfolio = {}  # Store holdings information
    initial_cash = 1000000  # Initial cash for backtesting and real-time trading
    cash = initial_cash  # Current cash available
    history = []  # Store portfolio value over time
    print("Strategy initialized.")

def fetch_stock_pool(date):
    """
    Fetch stock data and apply selection criteria for a specific date
    """
    stock_data = ak.stock_zh_a_spot_em()  # Fetch daily A-share market data
    
    # Filter based on criteria
    stock_data = stock_data[
        (stock_data['close'] > 1.5) &
        (stock_data['close'] < 9) &
        (stock_data['market_cap'] < 200 * 1e8)  # Convert market cap to Yuan
    ]
    
    # Filter top 25% by dividend yield
    stock_data['dividend_rank'] = stock_data['dividend_yield'].rank(pct=True, ascending=False)
    stock_data = stock_data[stock_data['dividend_rank'] <= 0.25]
    
    # Sort by market cap, ascending, and select top 10
    stock_data = stock_data.sort_values(by='market_cap').head(max_holdings)
    
    return stock_data['symbol'].tolist()

def update_portfolio(date):
    """
    Update portfolio by rebalancing holdings based on selection criteria
    """
    selected_stocks = fetch_stock_pool(date)
    
    # Sell stocks not in selected pool or that hit stop conditions
    for symbol in list(portfolio.keys()):
        current_price = get_stock_price(symbol, date)
        if symbol not in selected_stocks or portfolio[symbol]['holding_days'] >= max_days:
            profit = (current_price - portfolio[symbol]['buy_price']) / portfolio[symbol]['buy_price']
            if profit >= stop_gain or profit <= -stop_loss:
                sell_stock(symbol, current_price)
    
    # Buy new stocks
    for symbol in selected_stocks:
        if symbol not in portfolio and len(portfolio) < max_holdings:
            buy_stock(symbol, date)

def buy_stock(symbol, date):
    """
    Simulate a buy order for a stock
    """
    global cash
    current_price = get_stock_price(symbol, date)
    quantity = cash / max_holdings / current_price
    cash -= quantity * current_price
    portfolio[symbol] = {
        "buy_price": current_price,
        "quantity": quantity,
        "holding_days": 0
    }
    print(f"Buying {symbol} at {current_price} on {date}")

def sell_stock(symbol, current_price):
    """
    Simulate a sell order for a stock
    """
    global cash
    quantity = portfolio[symbol]["quantity"]
    cash += quantity * current_price
    print(f"Selling {symbol} at {current_price}")
    del portfolio[symbol]

def get_stock_price(symbol, date):
    """
    Fetch the closing price of a stock on a specific date
    """
    data = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=date, end_date=date)
    if not data.empty:
        return data['close'].iloc[0]
    return None

def update_profit(date):
    """
    Update holding days and calculate portfolio value
    """
    portfolio_value = cash
    for symbol in list(portfolio.keys()):
        current_price = get_stock_price(symbol, date)
        if current_price:
            portfolio[symbol]["holding_days"] += 1
            portfolio_value += portfolio[symbol]["quantity"] * current_price
    history.append({"date": date, "portfolio_value": portfolio_value})

def simulate_real_time():
    """
    Run the automated trading process for today's date
    """
    init()
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    print(f"Running automated trading for {today}")
    update_portfolio(today)
    update_profit(today)
    print("Automated trading completed. Portfolio value:", history[-1]["portfolio_value"])

def schedule_daily_run():
    """
    Schedule the automated trading function to run daily
    """
    # Schedule `simulate_real_time` to run daily at a specified time (e.g., 9:00 AM)
    schedule.every().day.at("09:00").do(simulate_real_time)
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Wait 1 minute before checking the schedule again

# Uncomment the line below to start automated daily trading
# schedule_daily_run()
