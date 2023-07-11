"""
    각종 indicator 지표들의 집합 파일
    각 indicator들의 상태는 어떤 exchange type이냐에 따라 변화한다.

    현재로는 crypto-stock 두 개의 지표 거래만 지원한다.
"""
import consts
import numpy as np


class IndicatorSettings:
    def __init__(self):
        pass


class GoldenCross:
    def __init__(self, indicator_string, candle_container, container_lock):
        self._indicator_string = indicator_string
        self._candle_container = candle_container
        self._container_lock = container_lock

    def get_sma(self, value):
        sma = np.sum(value) / len(value)

        return sma

    def calculate(self):
        with self._container_lock:
            short_close = self._candle_container.close
            long_close = self._candle_container.close


