"""
    각종 indicator 지표들의 집합 파일
    각 indicator들의 상태는 어떤 exchange type이냐에 따라 변화한다.

    현재로는 crypto-stock 두 개의 지표 거래만 지원한다.
"""
import numpy as np
import threading
from calc_module import CandleContainer
import re


class Settings:
    def __init__(self, indicator_string: str):
        self.algo_name, self.setting_words = re.findall('[\d\w]+', indicator_string)
        self.value = dict()

        self.define_settings()

    def define_settings(self) -> None:
        self.value = {
            "candle_size": self.setting_words[0],
            "method": self.setting_words[-1]
        }

        func = getattr(self, f"settings_{self.algo_name}")
        self.setting_words.update(func())

    def settings_bollinger_band(self):
        return {
            "period": int(self.setting_words[1]),
            "deviation": int(self.setting_words[2]),
            "reference": self.setting_words[3]
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
            "bound": int(self.setting_words[2]),
            "reference": self.setting_words[3]
        }

    def settings_cci(self):
        return {
            "period": int(self.setting_words[1]),
            "bound": int(self.setting_words[2])
        }


class BaseIndicator:
    def __init__(
            self,
            candle_container: CandleContainer,
            container_lock: threading.Lock,
            settings: Settings
    ):
        self._candle_container = candle_container
        self._container_lock = container_lock
        self._data_set = dict()
        self._settings = settings.value

    def get_sma(
            self,
            values: list
    ) -> float:
        sma = np.sum(values) / len(values)

        return sma

    def bound_checker(self) -> bool:
        if self._settings["method"] == "bound_upper":
            if self._settings["bound"] > self._data_set["latest"]:
                return True
        elif self._settings["method"] == "bound_lower":
            if self._settings["bound"] < self._data_set["latest"]:
                return True
        return False

    def cross_bound_checker(self) -> bool:
        if self._settings["method"] == "cross_bound_upper":
            if self._data_set["prev"] < self._settings["bound"] < self._data_set["latest"]:
                return True
        elif self._settings["method"] == "cross_bound_lower":
            if self._data_set["latest"] < self._settings["bound"] < self._data_set["prev"]:
                return True
        return False

    def check_values(self) -> bool:
        result = [
            self.bound_checker(),
            self.cross_bound_checker()
        ]
        return any(result)

    def calculator(self) -> None:
        # 추상화. 하위 객체에서 정의한다. 
        return None
    

class GoldenCross(BaseIndicator):
    def __init__(
            self,
            *args
    ):
        super().__init__(*args)

    def __repr__(self):
        return "goldencross"

    def check_values(self) -> bool:
        if not self._data_set:
            raise "정보가 없음"

        if self._data_set["prev_short"] >= self._data_set["prev_long"]:
            if self._data_set["short"] >= self._data_set["long"]:
                return True
        return False

    def calculator(self) -> None:
        with self._container_lock:
            close = self._candle_container.close

        short_close = close[:self._settings["short_period"]]
        long_close = close[:self._settings["long_period"]]

        prev_short_close = close[1:self._settings["short_period"] + 1]
        prev_long_close = close[1:self._settings["long_period"] + 1]

        short_sma = self.get_sma(short_close)
        long_sma = self.get_sma(long_close)
        prev_short_sma = self.get_sma(prev_short_close)
        prev_long_sma = self.get_sma(prev_long_close)

        self._data_set = {
            "short": short_sma,
            "long": long_sma,
            "prev_short": prev_short_sma,
            "prev_long": prev_long_sma
        }


class BollingerBand(BaseIndicator):
    def __init__(
            self,
            *args
    ):
        super().__init__(*args)

    def __repr__(self):
        return "bollingerband"

    def check_values(self) -> bool:
        reference = self._settings["reference"]
        if self._settings["method"] == "cross_bound_upper":
            # lower -> upper로 band가 cross된다..!

            if self._data_set["prev"]["candle"] < self._data_set["prev"][reference] \
                    and self._data_set["latest"]["candle"] > self._data_set[reference]:
                return True
        
        elif self._settings["method"] == "cross_bound_lower":
            # upper -> lower로 band가 cross된다..!
            if self._data_set["prev"]["candle"] > self._data_set["prev"][reference] \
                    and self._data_set["latest"]["candle"] < self._data_set[reference]:
                return True
        return False
        
    def get_band_index(self, candles: list):
        sma = self.get_sma(candles)
        deviation = self.get_deviation(candles)

        middle = sma
        upper = sma + (deviation * self._settings["deviation"])
        lower = sma - (deviation * self._settings["deviation"])

        return {
            "middle": middle,
            "upper": upper,
            "lower": lower,
        }

    def calculator(self) -> None:
        with self._container_lock:
            candles = self._candle_container.close[:]

        prev_dict = self.get_band_index(candles[:-1])
        latest_dict = self.get_band_index(candles[1:])

        prev_dict.update({"candle": 1})
        latest_dict.update({"candle": 0})

        self._data_set = {
            "prev": prev_dict,
            "latest": latest_dict
        }

    def get_deviation(self, candles: list) -> float:
        average = np.sum(candles) / len(candles)

        sub_average = np.subtract(candles, average)
        exponent = np.power(sub_average, 2)

        result = np.sum(exponent) / (len(candles) - 1)

        deviation = np.sqrt(abs(result))

        return deviation


class RSI(BaseIndicator):
    def __init__(
            self,
            *args
    ):
        super().__init__(*args)

    def __repr__(self):
        return "rsi"

    def calculator(self) -> None:
        with self._container_lock:
            candles = self._candle_container.close
        
        period = self._settings["period"]
        
        differences = np.array(candles['close'][1:]) - np.array(candles['close'][:-1])
        prev_average_gain = np.sum(differences[:period][differences[:period] > 0]) / period
        prev_average_loss = np.sum(differences[:period][differences[:period] < 0]) / period
        
        for diff in differences[period:-1]:
            prev_average_gain = ((prev_average_gain * (period - 1)) + (0 if diff < 0 else diff)) / period
            prev_average_loss = ((prev_average_loss * (period - 1)) - (0 if diff > 0 else diff)) / period

        prev_rsi = self.get_rsi(prev_average_gain, prev_average_loss)

        average_gain = ((prev_average_gain * (period - 1)) + (0 if differences[-1] < 0 else differences[-1])) / period
        average_loss = ((prev_average_loss * (period - 1)) - (0 if differences[-1] > 0 else differences[-1])) / period
        
        rsi = self.get_rsi(average_gain, average_loss)
        
        self._data_set = {
            "latest": rsi,
            "prev": prev_rsi
        }

    def get_rsi(self, gain, loss) -> float:
        rs = abs(gain / loss)

        rsi = 100 - (100 / (1 + rs))

        return rsi


class MACD(BaseIndicator):
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return "macd"

    def calculator(self) -> None:
        with self._container_lock:
            candles = self._candle_container.close
            
        sync = self._settings["long_period"] - self._settings["short_period"]
        short_ema_list = self.get_ema(candles, self._settings["short_period"])[sync:]
        long_ema_list = self.get_ema(candles, self._settings["long_period"])

        macd_line = np.array(short_ema_list) - np.array(long_ema_list)
        
        prev_macd_line = macd_line[:-1]

        signal_line = self.get_ema(macd_line, self._settings['signal_period'])
        prev_signal_line = signal_line[:-1]

        prev_macd_histogram = prev_macd_line[-1] - prev_signal_line[-1]
        macd_histogram = macd_line[-1] - signal_line[-1]

        if self._settings['reference'] == 'line':
            self._data_set = {
                'prev': prev_macd_line[-1],
                'latest': macd_line[-1],
            }

        elif self._settings['reference'] == 'histogram':
            self._data_set = {
                'prev': prev_macd_histogram,
                'latest': macd_histogram
            }
    def get_ema(self, candles, period):
        previous_ema = (np.sum(candles[:period]) / period)
        multipliers = (2 / (period + 1))
        ema_list = []

        for candle in candles[period+1:]:
            previous_ema = (candle - previous_ema) * multipliers + previous_ema

            ema_list.append(previous_ema)

        return ema_list


class Stochastic(BaseIndicator):
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return "stochastic"

    def calculator(self) -> None:
        with self._container_lock:
            high = self._candle_container.high
            low = self._candle_container.low
            close = self._candle_container.close

        period = self._settings["period"]

        highest = np.max(high[:period-1])
        lowest = np.min(low[:period-1])

        k_list = []
        for n in range(6):
            highest = max(highest, high[period - 1 + n])
            lowest = min(lowest, low[period - 1 + n])

            close_lowest = close[period - 1 + n] - lowest
            differ = highest - lowest

            k = (close_lowest / differ) * 100
            k_list.append(k)

        stochastic_list = []
        for n in range(4):
            stochastic_list.append(
                self.get_sma(k_list[n:n + 3])
            )
        slow_d = self.get_sma(stochastic_list[:2])
        prev_slow_d = self.get_sma(stochastic_list[:-1])

        if self._settings["reference"] == "fastk":
            self._data_set = {
                "prev": k_list[-2],
                "latest": k_list[-1]
            }
        else:
            self._data_set = {
                "prev": slow_d,
                "latest": prev_slow_d
            }


class CCI(BaseIndicator):
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return "cci"

    def calculator(self) -> None:
        with self._container_lock:
            close = self._candle_container.close
            high = self._candle_container.high
            low = self._candle_container.low

        period = self._settings["period"]

        sums = np.array(high + low + close)
        typical_price = np.divide(sums, 3)

        cci_list = []
        for n in range(2):
            period_sma = self.get_sma(typical_price[n:period + n])
            distance = np.absolute(np.subtract(period_sma, typical_price[n:period + n]))

            mean_deviation = np.sum(distance) / period
            subtract_typical = typical_price[-2 + n] - period_sma
            cci = np.divide(subtract_typical, 0.015 * mean_deviation)

            cci_list.append(cci)

        self._data_set = {
            "prev": cci_list[0],
            "latest": cci_list[1]
        }
