"""
    각종 indicator 지표들의 집합 파일
    각 indicator들의 상태는 어떤 exchange type이냐에 따라 변화한다.

    현재로는 crypto-stock 두 개의 지표 거래만 지원한다.
"""
import numpy as np
import threading
from objects import CandleContainer, Settings


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
    """
        입력받은 close data를 기반으로 다음을 구한다.
            1. 단기 이평선, 장기 이평선
            2. 전 단기 이평선, 전 장기 이평선
    """
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
        line = self._settings["line"]
        if self._settings["method"] == "cross_bound_upper":
            # 이전 perb는 line line(upper, lower, middle)을 넘지 않았음
            # 현재 perb는 line line(upper, lower, middle)을 넘은 상태임

            if self._data_set["prev"]["perb"] < self._data_set["prev"][line] \
                    and self._data_set["latest"]["preb"] > self._data_set[line]:
                return True
        
        elif self._settings["method"] == "cross_bound_lower":
            if self._data_set["prev"]["preb"] > self._data_set["prev"][line] \
                    and self._data_set["latest"]["preb"] < self._data_set[line]:
                return True
        return False
        
    def get_band_index(self, candles: list):
        """
            perb: 하한선에 위치한다면 0, 상한선에 위치한다면 1
        """
        sma = self.get_sma(candles)
        deviation = self.get_deviation(candles)

        middle = sma
        upper = sma + (deviation * self._settings["deviation"])
        lower = sma - (deviation * self._settings["deviation"])

        perb = (candles[0] - lower) / (upper - lower)
        band_width = (upper - lower) / middle

        return {
            "middle": middle,
            "upper": upper,
            "lower": lower,
            "perb": perb,
            "band_width": band_width
        }

    def get_deviation(self, candles: list) -> float:
        average = np.average(candles)

        sub_average = np.subtract(candles, average)
        exponent = np.power(sub_average, 2)

        variance = np.sum(exponent) / (len(candles) - 1)

        deviation = np.sqrt(abs(variance))

        return deviation

    def calculator(self) -> None:
        with self._container_lock:
            candles = self._candle_container.close

        prev_dict = self.get_band_index(candles[1:])
        latest_dict = self.get_band_index(candles)

        self._data_set = {
            "prev": prev_dict,
            "latest": latest_dict
        }


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
            close = self._candle_container.close

        period = self._settings["period"]
        period_m = self._settings["period_m"]
        period_t = self._settings["period_t"]

        close.reverse()
        k_list = []
        for n in range(period_m + period_t):
            # 0, 1, 2, 3, 4, 5
            latest = close[n]
            highest_by_period = np.max(close[n:period+n])
            lowest_by_period = np.min(close[n:period+n])

            raw_data = (latest - lowest_by_period) / (highest_by_period - lowest_by_period)

            fastk = raw_data * 100
            k_list.append(fastk)

        fast_d_list = []
        for d in range(period_m):
            # 0:3 1:4 2:5
            fast_d_list.append(self.get_sma([k_list[d:d+period_m]]))

        slow_d_list = []
        for sd in range(period_t):
            # 0:3 1:4 2:5
            slow_d_list.append(self.get_sma(slow_d_list[sd:sd+period_t]))

        if self._settings["reference"] == "fastk":
            self._data_set = {
                "prev": k_list[1],
                "latest": k_list[0]
            }
        elif self._settings["reference"] in ["fastd", "slowd"]:
            self._data_set = {
                "prev": fast_d_list[1],
                "latest": fast_d_list[0]
            }
        else:
            self._data_set = {
                "prev": slow_d_list[1],
                "latest": slow_d_list[0]
            }


class CCI(BaseIndicator):
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return "cci"

    def calculator(self) -> None:
        with self._container_lock:
            close = self._candle_container.close

        candle_size = self._settings["candle_size"]
        period = self._settings["period"]

        typical_price_list = []
        for n in range(0, len(close), candle_size):
            close_by_period = close[n:n+candle_size]

            high, low = max(close_by_period), min(close_by_period)
            latest = close_by_period[0]

            typical_price = (high + low + latest) / 3

            typical_price_list.append(typical_price)

        cci_list = []
        for n in range(2):
            period_sma = self.get_sma(typical_price_list[n:period + n])
            distance = np.absolute(np.subtract(period_sma, typical_price_list[n:period + n]))

            mean_deviation = np.sum(distance) / period
            subtract_typical = typical_price_list[-2 + n] - period_sma
            cci = np.divide(subtract_typical, 0.015 * mean_deviation)

            cci_list.append(cci)

        self._data_set = {
            "prev": cci_list[0],
            "latest": cci_list[1]
        }
