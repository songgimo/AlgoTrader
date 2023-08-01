from AlgoTrader.calculators import (
    StockRefresher,
    Stock
)

from AlgoTrader.indicators import IndicatorNode

from objects import CandleContainer

import threading
import time

import unittest


"""
BB, MACD, GC 확인 필요.
"""


class TestIndicators(unittest.TestCase):
    """
        golden cross:
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        test_orderbook = {
            '005930': [69900, 70000, 70000, 69900, 70000, 70000, 70000, 69900, 69900, 69900, 70000, 70000, 70000, 70000,
                       70000, 70000, 69900, 69900, 70000, 70000, 69900, 70000, 70000, 70000, 70000, 70000, 69900, 69900,
                       70000, 69900, 70000, 70000, 69900, 69900, 70000, 70000, 70000, 70000, 69900, 69900, 69900, 70000,
                       69900, 69900, 70000, 69900, 70000, 70000, 70000, 69900, 70000, 70000, 70000, 69900, 70000, 69900,
                       70000, 69900, 69900, 69900, 69900, 69900, 70000, 70000, 70000, 70000, 70000, 69900, 69900, 69900,
                       69900, 70000, 69900, 70000, 70000, 69900, 69900, 69900, 69900, 70000, 70000, 69900, 69900, 69900,
                       69900, 69900, 69900, 69900, 70000, 70000, 70000, 69900, 69900, 70000, 69900, 70000, 70000, 70000,
                       70000, 70000, 70000],
        }
        self._mock_history = {
            '005930': [
                ['20230801', '70100', '70000', '71200', '71100'],
                ['20230731', '70900', '69800', '71000', '-69800'],
                ['20230728', '71800', '70100', '72400', '-70600'],
                ['20230727', '69900', '69300', '71700', '+71700'],
                ['20230726', '69800', '68100', '70600', '-69800'],
                ['20230725', '70000', '69800', '70500', '-70000'],
                ['20230724', '70100', '69900', '70900', '+70400'],
                ['20230721', '70400', '69400', '70400', '-70300'],
                ['20230720', '71100', '70800', '71500', '-71000'],
                ['20230719', '72700', '71300', '72800', '-71700'],
                ['20230718', '73200', '72000', '73500', '-72000'],
                ['20230717', '73200', '72800', '73500', '-73300'],
                ['20230714', '72500', '72400', '73400', '+73400'],
                ['20230713', '72400', '71900', '72600', '71900'],
                ['20230712', '71200', '71100', '72000', '+71900'],
                ['20230711', '70200', '70100', '71500', '+71500'],
                ['20230710', '70000', '69200', '70400', '-69500'],
                ['20230707', '71100', '69800', '71400', '-69900'],
                ['20230706', '71900', '71500', '72400', '-71600'],
                ['20230705', '73000', '71900', '73300', '-72000'],
                ['20230704', '73400', '72900', '73600', '73000'],
                ['20230703', '72700', '72600', '73200', '+73000'],
                ['20230630', '72500', '71700', '72700', '-72200'],
                ['20230629', '73100', '72400', '73400', '-72400'],
                ['20230628', '72600', '72000', '72700', '+72700'],
                ['20230627', '72500', '72000', '72600', '+72600'],
                ['20230626', '71700', '71500', '72500', '+72400'],
                ['20230623', '72000', '71600', '72200', '+71600'],
                ['20230622', '70200', '70100', '71500', '+71300'],
                ['20230621', '70700', '70400', '71200', '-70500'],
                ['20230620', '70700', '70400', '71400', '+71400'],
                ['20230619', '71300', '70900', '71700', '-71200']
            ]
        }

        self.candle_container = CandleContainer("005930")
        self.lock = threading.Lock()

        self.candle_container.place_history_date_ohlc(self._mock_history["005930"])

        self.candle_container.open = 70100
        self.candle_container.low = 70000
        self.candle_container.high = 71200
        self.candle_container.close = 71100

        self._boolean = [True, False]

    def test_golden_cross(self):
        """
            golden cross
                - candle_size: 캔들의 규모 (실시간, 1분, 5분, 10분, 30분 등등)
                - short period: 단기 이동 평균 기간
                - long period: 장기 이동 평균 기간
                - method: 트리거 발생 조건

        """
        string_ = "GoldenCross[1, 14, 50, bound_upper]"

        indi_node = IndicatorNode(
            self.candle_container,
            self.lock,
            string_
        )

        result = self.t_by_indicator_class(indi_node.indicator_class)

        self.assertIn(result, self._boolean)

    def test_bollinger_band(self):
        """
            bollinger band
                - candle_size: 캔들의 규모 (실시간, 1분, 5분, 10분, 30분 등등)
                - period: 계산될 캔들의 갯수
                - deviation: 표준 편차 증폭 계수
                - line: lower, middle, upper의 트리거 라인 설정
                - method: 트리거 발생 조건
        """
        string_ = "BollingerBand[1, 14, 2, upper, bound_upper]"

        indi_node = IndicatorNode(
            self.candle_container,
            self.lock,
            string_
        )

        result = self.t_by_indicator_class(indi_node.indicator_class)

        self.assertIn(result, self._boolean)

    def test_rsi(self):
        """
            rsi
                - candle_size: 캔들의 규모 (실시간, 1분, 5분, 10분, 30분 등등)
                - period: 계산될 캔들의 갯수
                - bound: 숫자 형태의 트리거 라인 설정
                - method: 트리거 발생 조건
        """
        string_ = "RSI[1, 14, 30, bound_upper]"

        indi_node = IndicatorNode(
            self.candle_container,
            self.lock,
            string_
        )

        self.t_by_indicator_class(indi_node.indicator_class)

    def test_macd(self):
        """
            macd
                - candle_size: 캔들의 규모 (실시간, 1분, 5분, 10분, 30분 등등)
                - short_period: 단기 지수 이동 평균 기간
                - long_period: 장기 지수 이동 평균 기간
                - signal_period: MACD 시그널 지수 이동 평균 기간
                - bound: 숫자 형태의 트리거 라인 설정
                - reference: Histogram/Line의 참조할 지표 상세
                - method: 트리거 발생 조건
        """
        string_ = "MACD[1, 13, 26, 9, 100, Histogram, bound_upper]"

        indi_node = IndicatorNode(
            self.candle_container,
            self.lock,
            string_
        )

        self.t_by_indicator_class(indi_node.indicator_class)

    def test_stochastic(self):
        """
            stochastic
                - candle_size: 캔들의 규모 (실시간, 1분, 5분, 10분, 30분 등등)
                - period: 계산될 캔들의 갯수
                - period_m: fastD를 계산할 기간
                - period_t: slowD를 계산할 기간
                - bound: 숫자 형태의 트리거 라인 설정
                - reference: fastK, fastD, slowK, slowD의 참조할 지표 상세
                - method: 트리거 발생 조건

        """
        string_ = "Stochastic[1, 14, 3, 3, 50, fastK, bound_lower]"
        indi_node = IndicatorNode(
            self.candle_container,
            self.lock,
            string_
        )

        result = self.t_by_indicator_class(indi_node.indicator_class)

        self.assertIn(result, self._boolean)

    def test_cci(self):
        """
            cci
                - candle_size: 캔들의 규모 (실시간, 1분, 5분, 10분, 30분 등등)
                - period: 계산될 캔들의 갯수
                - reference: high, low, close가 계산될 candle의 range
                - bound: 숫자 형태의 트리거 라인 설정
                - method: 트리거 발생 조건

        """
        string_ = "CCI[1, 14, 50, 3, bound_upper]"
        indi_node = IndicatorNode(
            self.candle_container,
            self.lock,
            string_
        )

        result = self.t_by_indicator_class(indi_node.indicator_class)

        self.assertIn(result, self._boolean)

    def t_by_indicator_class(self, indi_class):
        indi_class.calculator()

        print(indi_class._data_set)

        result = indi_class.check_values()
        print(result)

        return result


class TStockRefresher:
    def __init__(self, thread_dict):
        self._stock_refresher = StockRefresher(thread_dict)

    def run_refresher(self):
        self._stock_refresher.run()
        while True:
            time.sleep(1)


class TestHistoryPlace(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mock_history = {
            '005930': [
                ['20230728', '71800', '70100', '72400', '-70600'],
                ['20230727', '69900', '69300', '71700', '+71700'],
                ['20230726', '69800', '68100', '70600', '-69800'],
                ['20230725', '70000', '69800', '70500', '-70000'],
                ['20230724', '70100', '69900', '70900', '+70400'],
                ['20230721', '70400', '69400', '70400', '-70300'],
                ['20230720', '71100', '70800', '71500', '-71000'],
                ['20230719', '72700', '71300', '72800', '-71700']
            ]
        }
        self._list_empty = []
        self._candle_container = CandleContainer("005930")
        self._candle_container.history_data = self._mock_history["005930"]
        self._candle_container.place_history_date_ohlc()

    def test_open_price_inserted(self):
        print(f"{self._candle_container.history_open=}")
        self.assertNotEqual(self._candle_container.history_open, self._list_empty)

    def test_high_price_inserted(self):
        print(f"{self._candle_container.history_high=}")
        self.assertNotEqual(self._list_empty, self._candle_container.history_high)

    def test_low_price_inserted(self):
        print(f"{self._candle_container.history_low=}")
        self.assertNotEqual(self._list_empty, self._candle_container.history_low)

    def test_close_price_inserted(self):
        print(f"{self._candle_container.history_close=}")
        self.assertNotEqual(self._list_empty, self._candle_container.history_close)


if __name__ == '__main__':
    unittest.main()