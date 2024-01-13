# 1. Object들에 대한 계산과 관련된 Thread 집합
# 2. 외부 Process/API와 상호작용을 하는 Thread 집합
# author: gimo
# date: 2023/07/30

import operator
import threading
import indicators
import time

from utils import REDIS_SERVER, DEBUG, CONFIG
from backup.StockApis.Kiwoom import consts as kiwoom_consts
from objects import CandleContainer


class Stock(threading.Thread):
    """
        Main Process로부터 실행되는 Thread.
        runner.py로부터 정의받은 두 개의 지표와 관련 인수를 받고 일치 여부를 판단한다.
        일치가 된다고 판단되면 Redis에 값을 포함한 거래 트리거를 세팅한다.
    """
    def __init__(
            self,
            container: CandleContainer,
            lock: threading.Lock,
            left: str,
            right: str,
            op: str
    ):
        super(Stock, self).__init__()
        self._candle_container = container
        self._candle_lock = lock

        self._left_indicator = indicators.IndicatorNode(self._candle_container, self._candle_lock, left)
        self._right_indicator = indicators.IndicatorNode(self._candle_container, self._candle_lock, right)

        self._op = getattr(operator, f"{op}_")

    def run(self) -> None:
        while True:
            left_indicator = self._left_indicator.indicator_class
            right_indicator = self._right_indicator.indicator_class

            left_indicator.calculator()
            right_indicator.calculator()

            left_val, right_val = left_indicator.check_values(), right_indicator.check_values()

            if self._op(left_val, right_val):
                data = {"symbol": self._candle_container.symbol}
                REDIS_SERVER.push(kiwoom_consts.RequestHeader.Trade, data)

            if DEBUG:
                print(left_indicator._data_set, right_indicator._data_set)
                print(left_val, right_val)
                time.sleep(5)


class StockRefresher(threading.Thread):
    """
        Main Process로부터 실행되는 Thread.
        runner.py로부터 정의된 thread_dict을 받고 적합한 data_container에 stock ohlc 값을 넣는다.
    """
    def __init__(self, thread_dict: dict):
        super().__init__()
        self._thread_dict = thread_dict

    def run(self) -> None:
        while True:
            stock_history_dict = REDIS_SERVER.get(kiwoom_consts.RequestHeader.Price)
            if stock_history_dict is None:
                time.sleep(0.1)
                continue

            for stock_code in stock_history_dict:
                if stock_code not in self._thread_dict.keys():
                    continue

                container = self._thread_dict[stock_code]["container"]
                with self._thread_dict[stock_code]["container_lock"]:
                    container.place_history_date_ohlc(stock_history_dict[stock_code])

                if DEBUG:
                    print(f"######### {stock_code} #########")
                    print(f"set, {container.history_open=}")
                    print(f"set, {container.history_close=}")
                    print(f"set, {container.history_low=}")
                    print(f"set, {container.history_high=}")

            break

        while True:
            current_price_dict = REDIS_SERVER.get(kiwoom_consts.RealReg.CurrentPrice)
            if current_price_dict is None:
                time.sleep(0.1)
                continue
            for stock_code in current_price_dict:
                if stock_code not in self._thread_dict.keys():
                    continue

                container = self._thread_dict[stock_code]["container"]
                with self._thread_dict[stock_code]["container_lock"]:
                    container.place_ohlc(current_price_dict[stock_code])

                if DEBUG:
                    print(f"######### {stock_code} #########")
                    print(f"set, {container.open=}, {container.low=}, {container.close=}, {container.high=}")

            if DEBUG:
                time.sleep(5)
            else:
                time.sleep(0.1)


if __name__ == '__main__':
    class TStockRefresher:
        def __init__(self, thread_dict):
            self._stock_refresher = StockRefresher(thread_dict)

        def run_refresher(self):
            self._stock_refresher.run()
            while True:
                time.sleep(1)

    def t_stock_refresh():
        lt = "Stochastic[1, 14, 3, 3, 50, fastK, bound_lower]"
        rt = "CCI[1, 14, 50, 3, bound_upper]"
        op = "and"

        symbol_list = CONFIG["kiwoom"]["codes"].split(";")
        thread_dict = dict()
        for symbol in symbol_list:
            container = CandleContainer(symbol)
            lock = threading.Lock()
            thread_dict[symbol] = {
                "container": container,
                "container_lock": lock,
                "thread": Stock(container, lock, lt, rt, op)
            }

        rt = TStockRefresher(thread_dict)
        rt.run_refresher()


    t_stock_refresh()
