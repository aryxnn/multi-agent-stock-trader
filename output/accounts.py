from typing import Dict, List, Optional, Any, Callable
import datetime


def get_share_price(symbol: str) -> float:
    """
    Returns the current share price for the provided stock symbol.

    Test implementation using fixed prices:
        - AAPL: $150.00
        - TSLA: $700.00
        - GOOGL: $2700.00

    Raises:
        ValueError: If the symbol is unrecognized.

    :param symbol: Stock ticker symbol
    :return: Current share price in USD
    """
    prices = {
        'AAPL': 150.0,
        'TSLA': 700.0,
        'GOOGL': 2700.0
    }
    if symbol not in prices:
        raise ValueError(f"Unknown symbol '{symbol}'")
    return prices[symbol]


class InsufficientFunds(Exception):
    """Raised when user attempts to withdraw or buy beyond available cash balance."""


class InsufficientShares(Exception):
    """Raised when user attempts to sell more shares than held."""


class InvalidTransaction(Exception):
    """Raised when transaction parameters are invalid, e.g., non-positive amounts or quantities."""


class Account:
    """
    Represents a user's trading account.

    Manages cash balance and multiple stock holdings, records transaction history,
    and facilitates fund deposits, withdrawals, and stock trades.

    Maintains initial deposit to calculate profit/loss.
    """

    cash_balance: float
    initial_deposit: float
    stock_holdings: Dict[str, int]
    transaction_history: List[Dict[str, Any]]
    _share_price_func: Callable[[str], float]

    def __init__(self, share_price_func: Optional[Callable[[str], float]] = None) -> None:
        """
        Initializes account with zero balance, empty holdings and no transactions.
        The share_price_func is the function to get current share price for a symbol,
        defaults to the module function get_share_price.
        """
        self.cash_balance = 0.0
        self.initial_deposit = 0.0
        self.stock_holdings = {}
        self.transaction_history = []
        self._share_price_func = share_price_func if share_price_func is not None else get_share_price

    def deposit(self, amount: float) -> None:
        """
        Add funds to the cash balance.

        :param amount: Amount in USD to deposit (must be > 0)
        :raises InvalidTransaction: if amount <= 0
        """
        if amount <= 0:
            raise InvalidTransaction("Deposit amount must be positive.")
        self.cash_balance += amount
        self.initial_deposit += amount
        self.transaction_history.append({
            'type': 'deposit',
            'symbol': None,
            'quantity': None,
            'price_per_share': None,
            'total_amount': amount,
            'timestamp': datetime.datetime.now(tz=datetime.timezone.utc)
        })

    def withdraw(self, amount: float) -> None:
        """
        Withdraw funds from the cash balance.

        Prevents overdraft (balance must remain >= 0).

        :param amount: Amount in USD to withdraw (must be > 0)
        :raises InvalidTransaction: if amount <= 0
        :raises InsufficientFunds: if withdrawal would cause negative balance
        """
        if amount <= 0:
            raise InvalidTransaction("Withdrawal amount must be positive.")
        if self.cash_balance - amount < 0:
            raise InsufficientFunds("Insufficient funds for withdrawal.")
        self.cash_balance -= amount
        self.transaction_history.append({
            'type': 'withdraw',
            'symbol': None,
            'quantity': None,
            'price_per_share': None,
            'total_amount': -amount,
            'timestamp': datetime.datetime.now(tz=datetime.timezone.utc)
        })

    def buy_shares(self, symbol: str, quantity: int) -> None:
        """
        Buy shares of a given stock symbol.

        Checks for sufficient cash balance to cover purchase.

        :param symbol: Stock ticker symbol (e.g. 'AAPL')
        :param quantity: Number of shares to buy (> 0)
        :raises InvalidTransaction: if quantity <= 0 or invalid symbol
        :raises InsufficientFunds: if cash balance insufficient
        """
        if quantity <= 0:
            raise InvalidTransaction("Buy quantity must be positive.")
        try:
            price = self._share_price_func(symbol)
        except ValueError:
            raise InvalidTransaction(f"Invalid stock symbol '{symbol}'")

        total_cost = price * quantity
        if self.cash_balance < total_cost:
            raise InsufficientFunds("Insufficient funds to buy shares.")
        self.cash_balance -= total_cost
        self.stock_holdings[symbol] = self.stock_holdings.get(symbol, 0) + quantity
        self.transaction_history.append({
            'type': 'buy',
            'symbol': symbol,
            'quantity': quantity,
            'price_per_share': price,
            'total_amount': -total_cost,
            'timestamp': datetime.datetime.now(tz=datetime.timezone.utc)
        })

    def sell_shares(self, symbol: str, quantity: int) -> None:
        """
        Sell shares of a given stock symbol.

        Checks user owns enough shares to sell.

        :param symbol: Stock ticker symbol
        :param quantity: Number of shares to sell (> 0)
        :raises InvalidTransaction: if quantity <= 0 or invalid symbol
        :raises InsufficientShares: if user does not have enough shares
        """
        if quantity <= 0:
            raise InvalidTransaction("Sell quantity must be positive.")
        try:
            price = self._share_price_func(symbol)
        except ValueError:
            raise InvalidTransaction(f"Invalid stock symbol '{symbol}'")

        owned = self.stock_holdings.get(symbol, 0)
        if owned < quantity:
            raise InsufficientShares("Insufficient shares to sell.")

        total_proceeds = price * quantity
        self.stock_holdings[symbol] = owned - quantity
        if self.stock_holdings[symbol] == 0:
            # Remove symbol if zero shares to keep dict clean
            del self.stock_holdings[symbol]
        self.cash_balance += total_proceeds
        self.transaction_history.append({
            'type': 'sell',
            'symbol': symbol,
            'quantity': quantity,
            'price_per_share': price,
            'total_amount': total_proceeds,
            'timestamp': datetime.datetime.now(tz=datetime.timezone.utc)
        })

    def get_portfolio_value(self) -> float:
        """
        Calculate the total value of the portfolio:
        cash balance + sum of (shares * current price) for all holdings.

        :return: total portfolio value in USD
        """
        total_value = self.cash_balance
        for symbol, qty in self.stock_holdings.items():
            try:
                price = self._share_price_func(symbol)
            except ValueError:
                # If symbol invalid at this time, treat price as 0 for portfolio valuation
                price = 0.0
            total_value += price * qty
        return total_value

    def get_profit_loss(self) -> float:
        """
        Compute profit or loss compared to the initial deposit amount.

        :return: Profit (positive) or Loss (negative) in USD.
        """
        return self.get_portfolio_value() - self.initial_deposit

    def get_holdings(self) -> List[Dict[str, Any]]:
        """
        Retrieve the current stock holdings as a detailed list.

        Each entry is a dict with:
            - 'symbol': str
            - 'quantity': int
            - 'current_price': float
            - 'total_value': float (quantity * current_price)

        Holdings with zero quantity are excluded.

        :return: List of stock holdings
        """
        holdings_list = []
        for symbol, qty in self.stock_holdings.items():
            if qty <= 0:
                continue
            try:
                current_price = self._share_price_func(symbol)
            except ValueError:
                current_price = 0.0
            holdings_list.append({
                'symbol': symbol,
                'quantity': qty,
                'current_price': current_price,
                'total_value': qty * current_price
            })
        return holdings_list

    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """
        Provide a copy of the full transaction history ordered chronologically.

        Useful for displaying user activity.

        :return: List of transaction dictionaries (as recorded)
        """
        return list(self.transaction_history)  # return a shallow copy to prevent external mutation