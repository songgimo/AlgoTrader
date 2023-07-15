import re
import threading
import consts
import indicators

from utils import REDIS_SERVER
from StockApis.Kiwoom import consts


class CandleContainer:
    def __init__(self):
        self.candle = []
        self.close = []
        self.high = []
        self.low = []


class IndicatorNode:
    def __init__(
            self,
            candle_container,
            candle_lock,
            val
    ):
        self._candle_container = candle_container
        self._candle_lock = candle_lock
        self.val = self.convert_string(val)

    def convert_string(self, val):
        data = re.findall("[\d\w]+", val.lower())

        name, indicate_data = data[0], data[1:]
        if consts.IndicatorName.GC in name:
            return indicators.GoldenCross(indicate_data, self._candle_container, self._candle_lock)

        elif consts.IndicatorName.BB in name:
            return indicators.BollingerBand(indicate_data, self._candle_container, self._candle_lock)

        elif consts.IndicatorName.RSI in name:
            return indicators.RSI(indicate_data, self._candle_container, self._candle_lock)

        elif consts.IndicatorName.MACD in name:
            return indicators.MACD(indicate_data, self._candle_container, self._candle_lock)

        elif consts.IndicatorName.STC in name:
            return indicators.Stochastic(indicate_data, self._candle_container, self._candle_lock)

        elif consts.IndicatorName.CCI in name:
            return indicators.CCI(indicate_data, self._candle_container, self._candle_lock)


class Stock(threading.Thread):
    def __init__(self, candle_container, stock_code, left, right):
        super(Stock, self).__init__()
        self._stock_code = stock_code

        self._candle_container = candle_container
        self._candle_lock = threading.Lock()

        self._left_indicator = IndicatorNode(self._candle_container, self._candle_lock, left)
        self._right_indicator = IndicatorNode(self._candle_container, self._candle_lock, right)

    def run(self) -> None:
        while True:
            if self._left_indicator.val.calculator() and self._right_indicator.val.calculator():
                pass


class Refresh(threading.Thread):
    def __init__(self, candle_container):
        super().__init__()
        self._candle_container = candle_container

    def run(self) -> None:
        while True:
            data = REDIS_SERVER.get(consts.RealReg.CurrentPrice)
            self._candle_container.close = data

