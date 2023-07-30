# 보조지표 계산과 관련된 object들의 집합
# 무엇인가를 실행하는 클래스는 없으며, 외부로부터 호출되어 사용되는 형태의 object 집합이다.
# author: gimo
# date: 2023/07/30


import numpy as np
import threading

from objects import CandleContainer, Settings
from utils import DEBUG
from AlgoTrader import consts as algo_consts


class IndicatorNode:
    """
        하위 보조지표를 wrapping하여 외부에서 사용할 수 있게 하는 클래스
        보조지표 클래스보다 상위에 위치하며, 외부와 통신한다.
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
            algo_consts.IndicatorName.GC: GoldenCross,
            algo_consts.IndicatorName.BB: BollingerBand,
            algo_consts.IndicatorName.RSI: RSI,
            algo_consts.IndicatorName.MACD: MACD,
            algo_consts.IndicatorName.STC: Stochastic,
            algo_consts.IndicatorName.CCI: CCI
        }
        setting_object = Settings(val)
        name = setting_object.algo_name

        indicator_class = class_dict.get(name, None)

        if indicator_class:
            return indicator_class(self._candle_container, self._candle_lock, setting_object)

        return None


class BaseIndicator:
    """
        보조지표의 중복된 함수와 변수를 정의한 상속 클래스
    """
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
        return np.sum(values) / len(values)

    def get_ema(
            self,
            candles: list,
            period: int
    ) -> list:
        # 지수 이동 평균, [oldest, ... latest]
        multipliers = (2 / (period + 1))

        reversed_data = list(reversed(candles[:period]))

        previous_ema = reversed_data[0]
        ema_list = [previous_ema]
        for candle in reversed_data[1:]:
            previous_ema = (candle * multipliers) + (previous_ema * (1 - multipliers))
            ema_list.append(previous_ema)

        return ema_list

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
        if DEBUG:
            print(self._settings)

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
            today_candles = self._candle_container.get_close_candles()
            yesterday_candles = self._candle_container.get_close_candles_without_today()

        short_close = today_candles[:self._settings["short_period"]]
        long_close = today_candles[:self._settings["long_period"]]

        prev_short_close = yesterday_candles[:self._settings["short_period"]]
        prev_long_close = yesterday_candles[:self._settings["long_period"]]

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
            today_candles = self._candle_container.get_close_candles()
            yesterday_candles = self._candle_container.get_close_candles_without_today()

        period = self._settings["period"]

        prev_dict = self.get_band_index(yesterday_candles[:period])
        latest_dict = self.get_band_index(today_candles[:period])

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

    def get_average_gain_loss(self, differences):
        gain = np.average(np.sum(differences[differences > 0])) / len(differences)
        loss = np.average(np.sum(differences[differences < 0])) / len(differences)

        return gain, loss

    def get_rsi(self, gain, loss) -> float:
        rs = abs(gain / loss)

        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculator(self) -> None:
        with self._container_lock:
            today_candles = self._candle_container.get_close_candles()

        period = self._settings["period"]
        
        differences = np.array(today_candles[:-1]) - np.array(today_candles[1:])

        latest_differences = differences[:period]
        prev_differences = differences[1:period+1]

        prev_average_gain, prev_average_loss = self.get_average_gain_loss(prev_differences)
        latest_average_gain, latest_average_loss = self.get_average_gain_loss(latest_differences)

        prev_rsi = self.get_rsi(prev_average_gain, prev_average_loss)
        rsi = self.get_rsi(latest_average_gain, latest_average_loss)
        
        self._data_set = {
            "latest": rsi,
            "prev": prev_rsi
        }


class MACD(BaseIndicator):
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return "macd"

    def calculator(self) -> None:
        with self._container_lock:
            today_candles = self._candle_container.get_close_candles()

        short_ema_list = self.get_ema(today_candles, self._settings["short_period"])
        long_ema_list = self.get_ema(today_candles, self._settings["long_period"])

        max_len = min(len(short_ema_list), len(long_ema_list))

        short_ema_list = short_ema_list[-max_len:]
        long_ema_list = long_ema_list[-max_len:]

        macd_line = np.array(short_ema_list) - np.array(long_ema_list)

        latest_macd_line = macd_line[-1]
        prev_macd_line = macd_line[-2]

        signal_line = self.get_ema(macd_line, self._settings['signal_period'])

        latest_signal_line = signal_line[-1]
        prev_signal_line = signal_line[-2]

        prev_macd_histogram = prev_macd_line - prev_signal_line
        latest_macd_histogram = latest_macd_line - latest_signal_line

        if self._settings['reference'] == 'line':
            self._data_set = {
                'prev': prev_macd_line,
                'latest': macd_line,
            }

        elif self._settings['reference'] == 'histogram':
            self._data_set = {
                'prev': prev_macd_histogram,
                'latest': latest_macd_histogram
            }


class Stochastic(BaseIndicator):
    def __init__(self, *args):
        super().__init__(*args)

    def __repr__(self):
        return "stochastic"

    def calculator(self) -> None:
        with self._container_lock:
            today_candles = self._candle_container.get_close_candles()

        period = self._settings["period"]
        period_m = self._settings["period_m"]
        period_t = self._settings["period_t"]

        today_candles.reverse()
        k_list = []
        for n in range(period_m + period_t):
            # 0, 1, 2, 3, 4, 5
            latest = today_candles[n]
            highest_by_period = np.max(today_candles[n:period+n])
            lowest_by_period = np.min(today_candles[n:period+n])

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
            today_close_list = self._candle_container.get_close_candles()
            today_high_list = self._candle_container.get_high_candles()
            today_low_list = self._candle_container.get_low_candles()

        period = self._settings["period"]

        typical_price_list = (today_high_list + today_low_list + today_close_list) / 3

        cci_list = []
        for n in range(2):
            period_sma = self.get_sma(typical_price_list[n:period + n])
            distance = typical_price_list[n:period + n] - period_sma
            mean_deviation = np.sum(np.absolute(distance)) / period
            cci = distance[0] / (0.015 * mean_deviation)

            cci_list.append(cci)

        self._data_set = {
            "prev": cci_list[0],
            "latest": cci_list[1]
        }
