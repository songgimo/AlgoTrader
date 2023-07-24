from AlgoTrader.calc_module import (
    IndicatorNode,
)

from objects import CandleContainer

import threading
import inspect


class TClass:
    """
        golden cross:
    """
    def __init__(self, candle_container):
        """
            candle spec
                GC: [candle_size, short_period, long_period, method]
                BB: [candle_size, period, deviation, line, method]
                RSI: [candle_size, period, bound, method]

                Stochastic: [candle_size, period, period_m, period_t, reference, method]
                    - reference: fastK, fastD, slowK, slowD
                CCI: [candle_size, period, bound, method]

        """
        self.candle_container = candle_container
        self.lock = threading.Lock()

        self.lt = "Stochastic[1, 14, 50, fastK, bound_lower]"
        self.rt = "GoldenCross[1, 14, 50, bound_upper]"
        self.op = "and"

    def total_test_in_indicators(self):
        for name, func in inspect.getmembers(self):
            if name.startswith("test"):
                print(f"start_function, {name}")
                result = func()
                print(result)

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

        self.test_by_indicator_class(indi_node.indicator_class)

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

        return self.test_by_indicator_class(indi_node.indicator_class)

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

        self.test_by_indicator_class(indi_node.indicator_class)

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

        self.test_by_indicator_class(indi_node.indicator_class)

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

        self.test_by_indicator_class(indi_node.indicator_class)

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

        self.test_by_indicator_class(indi_node.indicator_class)

    def test_by_indicator_class(self, indi_class):
        indi_class.calculator()

        print(indi_class._data_set)

        result = indi_class.check_values()
        print(result)

        return result


if __name__ == '__main__':
    test_orderbook = {
        '005930': [69900, 70000, 70000, 69900, 70000, 70000, 70000, 69900, 69900, 69900, 70000, 70000, 70000, 70000, 70000, 70000, 69900, 69900, 70000, 70000, 69900, 70000, 70000, 70000, 70000, 70000, 69900, 69900, 70000, 69900, 70000, 70000, 69900, 69900, 70000, 70000, 70000, 70000, 69900, 69900, 69900, 70000, 69900, 69900, 70000, 69900, 70000, 70000, 70000, 69900, 70000, 70000, 70000, 69900, 70000, 69900, 70000, 69900, 69900, 69900, 69900, 69900, 70000, 70000, 70000, 70000, 70000, 69900, 69900, 69900, 69900, 70000, 69900, 70000, 70000, 69900, 69900, 69900, 69900, 70000, 70000, 69900, 69900, 69900, 69900, 69900, 69900, 69900, 70000, 70000, 70000, 69900, 69900, 70000, 69900, 70000, 70000, 70000, 70000, 70000, 70000],
        '066570': [120700, 120700, 120700, 120700, 120700, 120600, 120700, 120600, 120700, 120600, 120700, 120700, 120600, 120600, 120600, 120600, 120600, 120700, 120700, 120600, 120600, 120700, 120700, 120600, 120700, 120600, 120600, 120700, 120600, 120700, 120600, 120600, 120700, 120600, 120600, 120700, 120700, 120700, 120700, 120700, 120700, 120700, 120600, 120700, 120600, 120700, 120700, 120700, 120700, 120700, 120700, 120700, 120700, 120700, 120600, 120700, 120600, 120600, 120600, 120700, 120700, 120700, 120700, 120700, 120600, 120600, 120700, 120700, 120700, 120700, 120700, 120700, 120700, 120700, 120600, 120600, 120600, 120700, 120700, 120700, 120700, 120700, 120600, 120700, 120600, 120600, 120600, 120700]
    }
    cd = CandleContainer("005930")
    cd.set_candle(test_orderbook["005930"])
    cd.set_close(test_orderbook["005930"])
    tc = TClass(cd)
    tc.test_cci()
