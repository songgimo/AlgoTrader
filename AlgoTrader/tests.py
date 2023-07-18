from AlgoTrader.calc_module import (
    IndicatorNode,
)

from objects import CandleContainer

import threading


class TestClass:
    def __init__(self):
        symbol = "005790"
        self.candle_container = CandleContainer(symbol)
        self.lock = threading.Lock()

        self.lt = "Stochastic[1, 14, 50, fastK, bound_lower]"
        self.rt = "CCI[1, 14, 50, bound_upper]"
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
        print(left, right)
        print(left.indicator_class, right.indicator_class)
        return left, right


if __name__ == '__main__':
    tc = TestClass()
    l, r = tc.indicator_node_checker()

