from accounts import Account, InsufficientFunds, InsufficientShares, InvalidTransaction
import gradio as gr
from datetime import timezone

# Initialize a single account instance for demo
account = Account()

# Allowed stock symbols for buy/sell
ALLOWED_SYMBOLS = ['AAPL', 'TSLA', 'GOOGL']

def deposit_funds(amount):
    try:
        amount_float = float(amount)
        account.deposit(amount_float)
        return "", f"Successfully deposited ${amount_float:.2f}!"
    except (InvalidTransaction, ValueError) as e:
        return amount, f"Error: {str(e)}"

def withdraw_funds(amount):
    try:
        amount_float = float(amount)
        account.withdraw(amount_float)
        return "", f"Successfully withdrew ${amount_float:.2f}!"
    except (InvalidTransaction, InsufficientFunds, ValueError) as e:
        return amount, f"Error: {str(e)}"

def buy_stocks(symbol, quantity_str):
    symbol = symbol.strip().upper()
    try:
        quantity = int(quantity_str)
        if symbol not in ALLOWED_SYMBOLS:
            return quantity_str, f"Error: Unknown stock symbol '{symbol}'!"
        account.buy_shares(symbol, quantity)
        return quantity_str, f"Successfully bought {quantity} shares of {symbol}!"
    except (InvalidTransaction, InsufficientFunds, ValueError) as e:
        return quantity_str, f"Error: {str(e)}"

def sell_stocks(symbol, quantity_str):
    symbol = symbol.strip().upper()
    try:
        quantity = int(quantity_str)
        if symbol not in ALLOWED_SYMBOLS:
            return quantity_str, f"Error: Unknown stock symbol '{symbol}'!"
        account.sell_shares(symbol, quantity)
        return quantity_str, f"Successfully sold {quantity} shares of {symbol}!"
    except (InvalidTransaction, InsufficientShares, ValueError) as e:
        return quantity_str, f"Error: {str(e)}"

def get_portfolio_table():
    holdings = account.get_holdings()
    rows = []
    for h in holdings:
        rows.append([
            h['symbol'],
            str(h['quantity']),
            f"${h['current_price']:.2f}",
            f"${h['total_value']:.2f}"
        ])
    return rows

def get_portfolio_summary():
    total_value = account.get_portfolio_value()
    profit_loss = account.get_profit_loss()
    cash = account.cash_balance
    return f"""Cash Balance: ${cash:.2f}<br>Total Portfolio Value: ${total_value:.2f}<br>Profit / Loss: ${profit_loss:.2f}"""

def get_transaction_history_table():
    txs = account.get_transaction_history()
    rows = []
    for tx in txs:
        ts = tx['timestamp'].astimezone().strftime('%Y-%m-%d %H:%M:%S')
        type_ = tx['type'].capitalize()
        symbol = tx['symbol'] if tx['symbol'] is not None else ''
        quantity = str(tx['quantity']) if tx['quantity'] is not None else ''
        price = f"${tx['price_per_share']:.2f}" if tx['price_per_share'] is not None else ''
        total = f"${tx['total_amount']:.2f}"
        rows.append([ts, type_, symbol, quantity, price, total])
    return rows

with gr.Blocks() as demo:
    gr.Markdown("## Trading Simulator Account Management Demo")

    with gr.Tab("Manage Cash"):
        with gr.Row():
            deposit_amount = gr.Textbox(label="Deposit Amount ($)", value="", interactive=True)
            deposit_btn = gr.Button("Deposit")
        with gr.Row():
            withdraw_amount = gr.Textbox(label="Withdraw Amount ($)", value="", interactive=True)
            withdraw_btn = gr.Button("Withdraw")

    with gr.Tab("Buy / Sell Stock"):
        with gr.Row():
            buy_symbol = gr.Dropdown(ALLOWED_SYMBOLS, label="Buy Stock Symbol", value="AAPL")
            buy_quantity = gr.Textbox(label="Buy Quantity", value="", interactive=True)
            buy_btn = gr.Button("Buy")
        with gr.Row():
            sell_symbol = gr.Dropdown(ALLOWED_SYMBOLS, label="Sell Stock Symbol", value="AAPL")
            sell_quantity = gr.Textbox(label="Sell Quantity", value="", interactive=True)
            sell_btn = gr.Button("Sell")

    with gr.Tab("Portfolio"):
        portfolio_summary = gr.HTML(get_portfolio_summary())
        portfolio_table = gr.Dataframe(headers=["Ticker", "Quantity", "Current Price", "Total Value"], datatype=["str","str","str","str"], interactive=False)

        refresh_portfolio_btn = gr.Button("Refresh Portfolio")

    with gr.Tab("Transaction History"):
        tx_table = gr.Dataframe(headers=["Timestamp", "Type", "Symbol", "Quantity", "Price per Share", "Total Amount"],
                               datatype=["str","str","str","str","str","str"], interactive=False)
        refresh_tx_btn = gr.Button("Refresh Transactions")

    status_box = gr.Textbox(label="Status / Notifications", interactive=False, value="", lines=2)

    # Callbacks for deposit and withdrawal
    deposit_btn.click(
        fn=deposit_funds,
        inputs=[deposit_amount],
        outputs=[deposit_amount, status_box]
    )

    withdraw_btn.click(
        fn=withdraw_funds,
        inputs=[withdraw_amount],
        outputs=[withdraw_amount, status_box]
    )

    # Buy/sell callbacks
    buy_btn.click(
        fn=buy_stocks,
        inputs=[buy_symbol, buy_quantity],
        outputs=[buy_quantity, status_box]
    )

    sell_btn.click(
        fn=sell_stocks,
        inputs=[sell_symbol, sell_quantity],
        outputs=[sell_quantity, status_box]
    )

    # Refresh Portfolio
    def refresh_portfolio():
        table_data = get_portfolio_table()
        summary_html = get_portfolio_summary()
        return summary_html, table_data

    refresh_portfolio_btn.click(
        fn=refresh_portfolio,
        inputs=[],
        outputs=[portfolio_summary, portfolio_table]
    )

    # Refresh transaction history
    def refresh_transactions():
        return get_transaction_history_table()

    refresh_tx_btn.click(
        fn=refresh_transactions,
        inputs=[],
        outputs=tx_table
    )

if __name__ == "__main__":
    demo.launch()