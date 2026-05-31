import unittest
from unittest.mock import patch
from accounts import Account, InsufficientFunds, InsufficientShares, InvalidTransaction

class TestAccount(unittest.TestCase):
    
    def setUp(self):
        # Patch get_share_price for all tests with deterministic prices
        patcher = patch('accounts.get_share_price')
        self.mock_get_price = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_get_price.side_effect = lambda symbol: {'AAPL': 100.0, 'TSLA': 200.0, 'GOOGL': 300.0}.get(symbol, (_ for _ in ()).throw(ValueError(f"Unknown symbol '{symbol}' )))
        self.account = Account(share_price_func=self.mock_get_price)

    def test_deposit_positive_amount(self):
        self.account.deposit(100.0)
        self.assertEqual(self.account.cash_balance, 100.0)
        self.assertEqual(self.account.initial_deposit, 100.0)
        self.assertEqual(len(self.account.transaction_history), 1)
        self.assertEqual(self.account.transaction_history[0]['type'], 'deposit')

    def test_deposit_zero_amount_invalid(self):
        with self.assertRaises(InvalidTransaction):
            self.account.deposit(0)

    def test_deposit_negative_amount_invalid(self):
        with self.assertRaises(InvalidTransaction):
            self.account.deposit(-50)

    def test_withdraw_valid(self):
        self.account.deposit(200)
        self.account.withdraw(150)
        self.assertEqual(self.account.cash_balance, 50)
        self.assertEqual(len(self.account.transaction_history), 2)
        self.assertEqual(self.account.transaction_history[1]['type'], 'withdraw')

    def test_withdraw_zero_amount_invalid(self):
        with self.assertRaises(InvalidTransaction):
            self.account.withdraw(0)
    
    def test_withdraw_negative_amount_invalid(self):
        with self.assertRaises(InvalidTransaction):
            self.account.withdraw(-10)

    def test_withdraw_insufficient_funds(self):
        self.account.deposit(100)
        with self.assertRaises(InsufficientFunds):
            self.account.withdraw(150)

    def test_buy_shares_valid(self):
        self.account.deposit(1000)  # enough cash
        self.account.buy_shares('AAPL', 5)  # price 100 * 5 = 500
        self.assertEqual(self.account.cash_balance, 500)
        self.assertEqual(self.account.stock_holdings['AAPL'], 5)
        self.assertEqual(len(self.account.transaction_history), 2)
        self.assertEqual(self.account.transaction_history[-1]['type'], 'buy')

    def test_buy_shares_zero_quantity_invalid(self):
        self.account.deposit(1000)
        with self.assertRaises(InvalidTransaction):
            self.account.buy_shares('AAPL', 0)

    def test_buy_shares_negative_quantity_invalid(self):
        self.account.deposit(1000)
        with self.assertRaises(InvalidTransaction):
            self.account.buy_shares('AAPL', -1)

    def test_buy_shares_insufficient_funds(self):
        self.account.deposit(100)  # not enough for 5 shares at 100 each (500)
        with self.assertRaises(InsufficientFunds):
            self.account.buy_shares('AAPL', 5)

    def test_buy_shares_invalid_symbol(self):
        self.account.deposit(1000)
        with self.assertRaises(InvalidTransaction):
            self.account.buy_shares('INVALID', 1)

    def test_sell_shares_valid(self):
        self.account.deposit(1000)
        self.account.buy_shares('AAPL', 5)
        self.account.sell_shares('AAPL', 3)
        self.assertEqual(self.account.stock_holdings['AAPL'], 2)
        self.assertEqual(self.account.cash_balance, 1000 - 500 + 300)  # after buy & sell
        self.assertEqual(len(self.account.transaction_history), 3)
        self.assertEqual(self.account.transaction_history[-1]['type'], 'sell')

    def test_sell_shares_zero_quantity_invalid(self):
        self.account.deposit(1000)
        self.account.buy_shares('AAPL', 5)
        with self.assertRaises(InvalidTransaction):
            self.account.sell_shares('AAPL', 0)

    def test_sell_shares_negative_quantity_invalid(self):
        self.account.deposit(1000)
        self.account.buy_shares('AAPL', 5)
        with self.assertRaises(InvalidTransaction):
            self.account.sell_shares('AAPL', -1)

    def test_sell_shares_insufficient_shares(self):
        self.account.deposit(1000)
        self.account.buy_shares('AAPL', 5)
        with self.assertRaises(InsufficientShares):
            self.account.sell_shares('AAPL', 10)

    def test_sell_shares_invalid_symbol(self):
        with self.assertRaises(InvalidTransaction):
            self.account.sell_shares('INVALID', 1)

    def test_get_portfolio_value(self):
        self.account.deposit(1000)
        self.account.buy_shares('AAPL', 5)  # 5 * 100 = 500
        val = self.account.get_portfolio_value()
        # Cash 1000 - 500 spent = 500 + stock value 500 = 1000
        self.assertAlmostEqual(val, 1000)

    def test_get_profit_loss(self):
        self.account.deposit(1000)
        self.account.buy_shares('AAPL', 5)  # spent 500
        self.account.sell_shares('AAPL', 5)  # get back 500
        profit_loss = self.account.get_profit_loss()
        self.assertAlmostEqual(profit_loss, 0)

    def test_get_holdings(self):
        self.account.deposit(1000)
        self.account.buy_shares('AAPL', 5)
        holdings = self.account.get_holdings()
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]['symbol'], 'AAPL')
        self.assertEqual(holdings[0]['quantity'], 5)
        self.assertEqual(holdings[0]['current_price'], 100.0)
        self.assertEqual(holdings[0]['total_value'], 500.0)

    def test_transaction_history_order_and_contents(self):
        self.account.deposit(500)
        self.account.withdraw(200)
        self.account.deposit(300)
        history = self.account.get_transaction_history()
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]['type'], 'deposit')
        self.assertEqual(history[1]['type'], 'withdraw')
        self.assertEqual(history[2]['type'], 'deposit')

if __name__ == '__main__':
    unittest.main()