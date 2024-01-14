import threading
from kiwoom.port import outbound


class AccountRefresherService(threading.Thread):
    def __init__(
            self,
            account
    ):
        super().__init__()
        self._account = account

    def set_account_info(self, port: outbound.KiwoomAPIPort) -> None:
        remaining_info = port.get_account_info(
            self._account.account_number,
        )

        cash_balance, stock_info = remaining_info["cash_balance"], remaining_info["stock_info"]

        self._account.set_cash_balance(cash_balance)
        self._account.set_stock_info(stock_info)

        return

