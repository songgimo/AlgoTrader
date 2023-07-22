from AlgoTrader.calc_module import (
    IndicatorNode,
)

from objects import CandleContainer

import threading
"""
test할것
    1. GoldenCross를 포함한 BaseIndicator들의 계산식 체크 필요.
"""


class TestClass:
    """
        golden cross:
    """
    def __init__(self, candle_container):
        """
            candle spec
                GC: [candle_size, short_period, long_period, method]
                Stochastic: [candle_size, period, period_m, period_t, reference, method]
                    - reference: fastK, fastD, slowK, slowD

        """
        self.candle_container = candle_container
        self.lock = threading.Lock()

        self.lt = "Stochastic[1, 14, 50, fastK, bound_lower]"
        self.rt = "GoldenCross[1, 14, 50, bound_upper]"
        self.op = "and"

    def indicator_node_checker(self):
        left = IndicatorNode(
            self.candle_container,
            self.lock,
            self.lt
        )

        right = IndicatorNode(
            self.candle_container,
            self.lock,
            self.rt
        )

        right_result = self.test_by_indicator_class(right.indicator_class)
        left_result = self.test_by_indicator_class(left.indicator_class)

        return left_result, right_result

    def test_by_indicator_class(self, indi_class):
        indi_class.calculator()

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
    tc = TestClass(cd)
    l, r = tc.indicator_node_checker()
