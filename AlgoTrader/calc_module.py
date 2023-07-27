import operator
import threading
import indicators
import time

from utils import REDIS_SERVER, DEBUG
from AlgoTrader import consts as algo_consts
from StockApis.Kiwoom import consts as kiwoom_consts
from objects import CandleContainer


class IndicatorNode:
    """
        최초 Stock Thread로부터 불러와지고 핸들링된다.
        유저로부터 입력된 보조지표 string값과 parameter를 입력받고 가공한다.
        이후 지표 Object를 가져오고 Stock Thread로 리턴되며, 조작된다.
    """
    def __init__(
            self,
            candle_container: CandleContainer,
            candle_lock: threading.Lock,
            val: str
    ):
        self._candle_container = candle_container
        self._candle_lock = candle_lock

        self.indicator_class = self.convert_string(val)

    def convert_string(self, val: str):
        class_dict = {
            algo_consts.IndicatorName.GC: indicators.GoldenCross,
            algo_consts.IndicatorName.BB: indicators.BollingerBand,
            algo_consts.IndicatorName.RSI: indicators.RSI,
            algo_consts.IndicatorName.MACD: indicators.MACD,
            algo_consts.IndicatorName.STC: indicators.Stochastic,
            algo_consts.IndicatorName.CCI: indicators.CCI
        }
        setting_object = indicators.Settings(val)
        name = setting_object.algo_name

        indicator_class = class_dict.get(name, None)

        if indicator_class:
            return indicator_class(self._candle_container, self._candle_lock, setting_object)

        return None


class Stock(threading.Thread):
    """
        main process로부터 핸들링되는 Thread이며, 트레이딩할 거래 지표를 정의한다.
        이후 지속적으로 N개의 인디케이터를 감시하고 트리거가 발동하는 경우 Kiwoom으로 거래 트리거를 보낸다.
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

        self._left_indicator = IndicatorNode(self._candle_container, self._candle_lock, left)
        self._right_indicator = IndicatorNode(self._candle_container, self._candle_lock, right)

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
    def __init__(self, thread_dict: dict):
        super().__init__()
        self._thread_dict = thread_dict

    def run(self) -> None:
        while True:
            current_price_dict = REDIS_SERVER.get(kiwoom_consts.RealReg.CurrentPrice)
            if current_price_dict is None:
                time.sleep(0.1)

            for stock_code in current_price_dict:
                if stock_code not in self._thread_dict.keys():
                    continue

                container = self._thread_dict[stock_code]["container"]
                price_data = current_price_dict[stock_code]

                container.close = price_data

