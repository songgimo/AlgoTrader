import re


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

    def set_candle(self, value):
        self.candle = value

    def set_close(self, value):
        self.close = value


class Settings:
    def __init__(self, indicator_string: str):
        self._indicator_string = re.findall('[\d\w]+', indicator_string)
        self.algo_name, self.setting_words = self._indicator_string[0].lower(), self._indicator_string[1:]
        self.value = dict()

        self.define_settings()

    def define_settings(self) -> None:
        self.value = {
            "candle_size": self.setting_words[0],
            "method": self.setting_words[-1]
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
            "line": self.setting_words[3]
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
            "reference": self.setting_words[5]
        }

    def settings_stochastic(self):
        return {
            "period": int(self.setting_words[1]),
            "period_m": int(self.setting_words[2]),
            "period_t": int(self.setting_words[3]),
            "reference": self.setting_words[4]
        }

    def settings_cci(self):
        return {
            "period": int(self.setting_words[1]),
            "bound": int(self.setting_words[2])
        }
