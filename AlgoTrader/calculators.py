# 1. Object들에 대한 계산과 관련된 Thread 집합
# 2. 외부 Process/API와 상호작용을 하는 Thread 집합
# author: gimo
# date: 2023/07/30

import operator
import threading
import indicators
import time

from utils import REDIS_SERVER, DEBUG
from StockApis.Kiwoom import consts as kiwoom_consts
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
                REDIS_SERVER.set(kiwoom_consts.RequestHeader.Trade, data)

            if DEBUG:
                print(left_val, right_val)
                time.sleep(10)


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
                    container.place_history_date_ohlc()

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

            time.sleep(0.1)
