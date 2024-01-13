import numpy as np
from algo_trader.port import outbound
from typing import List, Dict, Union


class BaseIndicator:
    def get_name(self):
        return self.__repr__()

    def calculator(self, port) -> dict:
        raise

    def check_values(self, data_set) -> bool:
        raise

    def get_sma(
            self,
            values: list
    ) -> float:
        return np.sum(values) / len(values)

    def get_ema(
            self,
            candles: List[float],
    ) -> list:
        multipliers = 2 / (len(candles) + 1)
        reversed_candles = list(reversed(candles))
        previous_ema = reversed_candles[0]
        ema_list = [previous_ema]
        for n, cp in enumerate(reversed_candles[1:]):
            previous_ema = (cp * multipliers) + (previous_ema * (1 - multipliers))
            ema_list.append(previous_ema)

        ema_list.reverse()

        return ema_list


class GoldenCross(BaseIndicator):
    def __init__(self, settings: Dict[str, Union[str, int, float]]):
        super().__init__()
        self._settings = settings

    def __repr__(self):
        return "goldencross"


class BollingerBand(BaseIndicator):
    def __init__(self, settings: Dict[str, Union[str, int, float]]):
        super().__init__()
        self._settings = settings

    def __repr__(self):
        return "bollingerband"

    def check_values(self, data_set) -> bool:
        pass

    def calculator(self, port: outbound.KiwoomAPIPort) -> dict:
        period = 14
        candles = port.get_close_candles_by_period(
            period
        )
        yesterday_candles = port.get_yesterday_close_candles_by_period(
            period
        )

        yesterday_band_index = self._get_indicator(yesterday_candles)
        band_index = self._get_indicator(candles)

        return {
            "prev": yesterday_band_index,
            "latest": band_index
        }

    def _get_indicator(self, candles: List[float]) -> dict:
        sma = self.get_sma(candles)
        deviation = self._get_deviation(candles)

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

    def _get_deviation(self, candles: List[float]) -> float:
        average = np.average(candles)

        sub_average = np.subtract(candles, average)
        exponent = np.power(sub_average, 2)

        variance = np.sum(exponent) / (len(candles) - 1)

        deviation = np.sqrt(abs(variance))

        return deviation
