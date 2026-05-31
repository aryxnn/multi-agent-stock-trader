```markdown
# Design Specification for `accounts.py`

## Overview

This module implements a simple account management system for a trading simulation platform that supports multiple stock symbols. It provides an `Account` class to manage user balances, stock holdings, and transaction history, enforcing business rules to prevent invalid operations such as overdrawing cash or selling shares not owned.

The module also includes:
- A fixed-price implementation of `get_share_price(symbol: str) -> float`
- Custom exception classes to explicitly signal error scenarios.
- Fully typed methods and attributes for clarity and maintainability.
- All functionality is self-contained and ready for direct integration or UI binding.

---

## Module-Level Function

```python
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
```

---

## Custom Exceptions

```python
class InsufficientFunds(Exception):
    """Raised when user attempts to withdraw or buy beyond available cash balance."""

class InsufficientShares(Exception):
    """Raised when user attempts to sell more shares than held."""

class InvalidTransaction(Exception):
    """Raised when transaction parameters are invalid, e.g., non-positive amounts or quantities."""
```

---

## `Account` Class Design

```python
class Account:
    """
    Represents a user's trading account.

    Manages cash balance and multiple stock holdings, records transaction history,
    and facilitates fund deposits, withdrawals, and stock trades.

    Maintains initial deposit to calculate profit/loss.
    """

    # --- Fields / Attributes ---

    cash_balance: float
        # Current cash balance available for trading.

    initial_deposit: float
        # Total amount of funds deposited to the account initially or cumulatively.

    stock_holdings: Dict[str, int]
        # Maps stock symbol to quantity of shares currently held (quantity >= 0).

    transaction_history: List[Dict[str, Any]]
        # Chronological list of all transactions, where each transaction is a dict with keys:
        #   - 'type': str ('deposit', 'withdraw', 'buy', 'sell')
        #   - 'symbol': Optional[str] (None for cash transactions)
        #   - 'quantity': Optional[int] (shares bought/sold; None for cash transactions)
        #   - 'price_per_share': Optional[float]
        #   - 'total_amount': float (positive for deposit/buy, negative for withdraw/sell)
        #   - 'timestamp': datetime.datetime

    # --- Constructor ---

    def __init__(self) -> None:
        """
        Initializes account with zero balance, empty holdings and no transactions.
        """
        ...

    # --- Account Management Methods ---

    def deposit(self, amount: float) -> None:
        """
        Add funds to the cash balance.

        :param amount: Amount in USD to deposit (must be > 0)
        :raises InvalidTransaction: if amount <= 0
        """
        ...

    def withdraw(self, amount: float) -> None:
        """
        Withdraw funds from the cash balance.

        Prevents overdraft (balance must remain >= 0).

        :param amount: Amount in USD to withdraw (must be > 0)
        :raises InvalidTransaction: if amount <= 0
        :raises InsufficientFunds: if withdrawal would cause negative balance
        """
        ...

    # --- Stock Trading Methods ---

    def buy_shares(self, symbol: str, quantity: int) -> None:
        """
        Buy shares of a given stock symbol.

        Checks for sufficient cash balance to cover purchase.

        :param symbol: Stock ticker symbol (e.g. 'AAPL')
        :param quantity: Number of shares to buy (> 0)
        :raises InvalidTransaction: if quantity <= 0 or invalid symbol
        :raises InsufficientFunds: if cash balance insufficient
        """
        ...

    def sell_shares(self, symbol: str, quantity: int) -> None:
        """
        Sell shares of a given stock symbol.

        Checks user owns enough shares to sell.

        :param symbol: Stock ticker symbol
        :param quantity: Number of shares to sell (> 0)
        :raises InvalidTransaction: if quantity <= 0 or invalid symbol
        :raises InsufficientShares: if user does not have enough shares
        """
        ...

    # --- Reporting Methods ---

    def get_portfolio_value(self) -> float:
        """
        Calculate the total value of the portfolio:
        cash balance + sum of (shares * current price) for all holdings.

        :return: total portfolio value in USD
        """
        ...

    def get_profit_loss(self) -> float:
        """
        Compute profit or loss compared to the initial deposit amount.

        :return: Profit (positive) or Loss (negative) in USD.
        """
        ...

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
        ...

    def get_transaction_history(self) -> List[Dict[str, Any]]:
        """
        Provide a copy of the full transaction history ordered chronologically.

        Useful for displaying user activity.

        :return: List of transaction dictionaries (as recorded)
        """
        ...
```

---

## Critical Logic Boundaries & Constraints

- **Cash balance must never be negative**  
  Withdrawals and purchases that would result in negative cash balance raise `InsufficientFunds`.

- **Share quantity held must never be negative**  
  Attempting to sell more shares than currently held raises `InsufficientShares`.

- **All transactions must have valid positive amounts or quantities**  
  Zero or negative values in deposits, withdrawals, purchases, or sales raise `InvalidTransaction`.

- **Stock symbols are validated against `get_share_price` availability**  
  If `get_share_price(symbol)` raises `ValueError`, the transaction is invalid.

---

## Additional Notes for Integration

- The transaction history timestamps should use `datetime.datetime.now()` in UTC timezone for consistency.

- Monetary amounts should be handled as `float` but could be enhanced with `decimal.Decimal` for precision if needed in future.

- The module is designed so that the UI can call:
  - Deposit, Withdraw, Buy, Sell methods and catch exceptions for user notifications.
  - Query holdings via `get_holdings()` to render the portfolio table (Ticker, Quantity, Current Price, Total Value).
  - Query profit/loss and portfolio value for display.
  - Query transaction history for detailed logs.

---

## Example Transaction Record Structure

```python
{
    'type': 'buy',              # 'buy', 'sell', 'deposit', 'withdraw'
    'symbol': 'AAPL',           # None for cash transactions
    'quantity': 10,             # None for cash transactions
    'price_per_share': 150.0,   # None for cash transactions
    'total_amount': -1500.0,    # Negative for cash spent or funds withdrawn; positive for deposits or proceeds from sale
    'timestamp': datetime.datetime(2024, 6, 14, 12, 30, 45, tzinfo=datetime.timezone.utc)
}
```

---

This completes the detailed design documentation for the `accounts.py` module and `Account` class, fully specifying how the backend developer should implement the account management system with stock trading functionality and proper safeguards.

```
# End of Design Spec