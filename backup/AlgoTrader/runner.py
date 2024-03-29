# 지표와 인수를 정의하고 실행하는 파일.
# 관련 스레드를 실행한다.
# author: gimo
# date: 2023/07/30

from calculators import Stock, StockRefresher
from objects import CandleContainer
from utils import REDIS_SERVER, CONFIG, DEBUG

import threading
import time


class AlgoRunner(threading.Thread):
    def __init__(self, symbol_list: str, left: str, right: str, op: str):
        super().__init__()
        self.symbol_list = symbol_list.split(";")
        self.thread_dict = dict()

        self.left = left.replace(" ", "")
        self.right = right.replace(" ", "")
        self.op = op

        self.set_stock_threads()

        self.refresher = StockRefresher(self.thread_dict)

        self.event = threading.Event()

    def set_stock_threads(self):
        for symbol in self.symbol_list:
            container = CandleContainer(symbol)
            lock = threading.Lock()
            self.thread_dict[symbol] = {
                "container": container,
                "container_lock": lock,
                "thread": Stock(container, lock, self.left, self.right, self.op)
            }

    def run(self) -> None:
        self.refresher.start()

        for symbol in self.thread_dict.keys():
            self.thread_dict[symbol]["thread"].start()
            time.sleep(0.1)

        self.event.wait()


if __name__ == '__main__':
    lt = "Stochastic[1, 14, 3, 3, 50, fastK, bound_lower]"
    rt = "CCI[1, 14, 50, 3, bound_upper]"
    op = "and"

    runner = AlgoRunner(
        CONFIG["kiwoom"]["codes"],
        lt,
        rt,
        op
    )

    runner.start()
