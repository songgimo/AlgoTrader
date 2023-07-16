import operator
import threading
import consts
import indicators

from utils import REDIS_SERVER
from StockApis.Kiwoom import consts


class CandleContainer:
    """
        Candle의 OHLC값이 들어간다.
        Refresh Thread를 통해 지속적으로 Write된다.
        Indicator들로부터 Read된다.
    """
    def __init__(self, symbol: str):
        # symbol은 005790같은 주식 코드 값이나, eth같은 symbol값이 입력된다.
        self.symbol = symbol

        self.candle = []
        self.close = []
        self.high = []
        self.low = []


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
            consts.IndicatorName.GC: indicators.GoldenCross,
            consts.IndicatorName.BB: indicators.BollingerBand,
            consts.IndicatorName.RSI: indicators.RSI,
            consts.IndicatorName.MACD: indicators.MACD,
            consts.IndicatorName.STC: indicators.Stochastic,
            consts.IndicatorName.CCI: indicators.CCI
        }
        setting_object = indicators.Settings(val)
        name = setting_object.algo_name

        indicator_class = class_dict.get(name, None)

        if indicator_class:
            return indicator_class(setting_object, self._candle_container, self._candle_lock)

        return None


class Stock(threading.Thread):
    """
        main process로부터 핸들링되는 Thread이며, 트레이딩할 거래 지표를 정의한다.
        이후 지속적으로 N개의 인디케이터를 감시하고 트리거가 발동하는 경우 Kiwoom으로 거래 트리거를 보낸다.
    """
    def __init__(self, container, lock, left, right, op):
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

            if self._op(left_indicator.check_values(), right_indicator.check_values()):
                data = {"symbol": self._candle_container.symbol}
                REDIS_SERVER.set(consts.RequestHeader.Trade, data)


class StockRefresher(threading.Thread):
    def __init__(self, thread_dict):
        super().__init__()
        self._thread_dict = thread_dict

    def run(self) -> None:
        while True:
            current_price_dict = REDIS_SERVER.get(consts.RealReg.CurrentPrice)

            for stock_code in current_price_dict:
                if stock_code not in self._thread_dict.keys():
                    continue

                container = self._thread_dict[stock_code]["container"]
                price_data = current_price_dict[stock_code]

                container.close = price_data

