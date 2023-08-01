# 외부로부터 사용되는 object들의 집합.
# 개별적인 카테고리 집합으로 묶기 어려운 클래스들의 집합.
# author: gimo
# date: 2023/07/30


import re
import datetime

import numpy as np


class CandleContainer:
    """
        Candle의 OHLC값이 들어간다.
        Refresh Thread를 통해 지속적으로 Write된다.
        Indicator들로부터 Read된다.
    """
    def __init__(self, symbol: str):
        # symbol은 005790같은 주식 코드 값이나, eth같은 symbol값이 입력된다.
        self.symbol = symbol

        self.candles = []
        self.open = 0
        self.close = 0
        self.high = 0
        self.low = 0

        self.history_data = []

        self.history_datetime = []
        self.history_open = []
        self.history_close = []
        self.history_high = []
        self.history_low = []

    def place_history_date_ohlc(self):
        for each in self.history_data:
            date_, open_, low, high, close = each
            self.history_datetime.append(datetime.datetime.strptime(date_, "%Y%m%d"))
            self.history_open.append(int(open_))
            self.history_low.append(int(low))
            self.history_high.append(int(high))
            self.history_close.append(abs(int(close)))

    def place_ohlc(self, price_dict):
        self.candles = price_dict["candles"]
        self.close = price_dict["close"]
        self.open = price_dict["open"]
        self.high = price_dict["high"]
        self.low = price_dict["low"]

    def get_open_candles(self):
        return np.array([
            self.open,
            *self.history_open[1:]
        ])

    def get_high_candles(self):
        return np.array([
            self.high,
            *self.history_high[1:]
        ])

    def get_low_candles(self):
        return np.array([
            self.low,
            *self.history_low[1:]
        ])

    def get_close_candles(self):
        return np.array([
            self.close,
            *self.history_close[1:]
        ])

    def get_close_candles_without_today(self):
        return np.array(self.history_close[1:-1])


class Settings:
    def __init__(self, indicator_string: str):
        self._indicator_string = re.findall('[\d\w]+', indicator_string)
        self.algo_name, self.setting_words = self._indicator_string[0].lower(), self._indicator_string[1:]
        self.value = dict()

        self.define_settings()

    def define_settings(self) -> None:
        self.value = {
            "candle_size": int(self.setting_words[0]),
            "method": self.setting_words[-1].lower()
        }

        func = getattr(self, f"settings_{self.algo_name}")
        self.value.update(func())

    def settings_goldencross(self):
        return {
            "short_period": int(self.setting_words[1]),
            "long_period": int(self.setting_words[2])
        }

    def settings_bollingerband(self):
        return {
            "period": int(self.setting_words[1]),
            "deviation": int(self.setting_words[2]),
            "line": self.setting_words[3].lower()
        }

    def settings_rsi(self):
        return {
            "period": int(self.setting_words[1]),
            "bound": int(self.setting_words[2])
        }

    def settings_macd(self):
        return {
            "short_period": int(self.setting_words[1]),
            "long_period": int(self.setting_words[2]),
            "signal_period": int(self.setting_words[3]),
            "bound": int(self.setting_words[4]),
            "reference": self.setting_words[5].lower()
        }

    def settings_stochastic(self):
        return {
            "period": int(self.setting_words[1]),
            "period_m": int(self.setting_words[2]),
            "period_t": int(self.setting_words[3]),
            "bound": int(self.setting_words[4]),
            "reference": self.setting_words[5].lower()
        }

    def settings_cci(self):
        return {
            "period": int(self.setting_words[1]),
            "bound": int(self.setting_words[2]),
            "reference": int(self.setting_words[3])
        }
