import threading

from PyQt5.QtWidgets import QApplication
from StockApis.Kiwoom.runner import Runner
from StockApis.Kiwoom import receiver, controllers, consts

from utils import REDIS_SERVER, CONFIG, DEBUG

import json
import time


class BasicRunning(threading.Thread):
    def __init__(self):
        super().__init__()
        self._runner = Runner()
        self._runner.start_communicators()

    def test_trade_signal_buy(self):
        data = {"symbol": "005930", "price": "69900", "trade_type": "buy"}
        REDIS_SERVER.push(consts.RequestHeader.Trade, data)

    def test_trade_signal_sell(self):
        data = {"symbol": "005930", "price": "69900", "trade_type": "sell"}
        REDIS_SERVER.push(consts.RequestHeader.Trade, data)

    def test_get_history_data(self):
        data = REDIS_SERVER.get(consts.RequestHeader.Price)
        print(data)

    def test_account_refresh(self):
        for i in range(60):
            if not i % 10:
                self.test_trade_signal_buy()
            else:
                self.test_trade_signal_sell()

            print(
                self._runner._account_refresher.account.account_info.stock_info,
                self._runner._account_refresher.account.account_info.cash_balance
            )
            time.sleep(5)

    def run(self) -> None:
        # exec_로 인한 시간차 테스팅 시작
        while not self._runner._sender.ready_flag:
            time.sleep(1)

        time.sleep(10)

        print("##### ##### ##### #####")
        print("##### Start Test! #####")
        print("##### ##### ##### #####")
        self.test_account_refresh()


if __name__ == '__main__':
    app = QApplication([])
    br = BasicRunning()
    br.start()

    app.exec_()
