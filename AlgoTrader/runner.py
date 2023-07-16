from calc_module import CandleContainer, Stock, StockRefresher

import threading
import time


class AlgoRunner(threading.Thread):
    def __init__(self, symbol_list: str, left: str, right: str, op: str):
        """
        """
        super().__init__()
        self.symbol_list = symbol_list.split(";")
        self.thread_dict = dict()

        self.left = left.replace(" ", "")
        self.right = right.replace(" ", "")
        self.op = op

        self.run_stock_threads()

        self.refresher = StockRefresher(self.thread_dict)

    def run_stock_threads(self):
        for symbol in self.symbol_list:
            container = CandleContainer(symbol)
            lock = threading.Lock()
            self.thread_dict[symbol] = {
                "container": container,
                "container_lock": lock,
                "thread": Stock(container, lock, self.op, self.left, self.right)
            }

            self.thread_dict[symbol]["thread"].start()

    def run(self) -> None:
        self.refresher.start()

        for symbol in self.thread_dict.keys():
            self.thread_dict[symbol]["thread"].start()
            time.sleep(0.1)

        while True:
            time.sleep(1)


if __name__ == '__main__':
    lt = "Stochastic[1, 14, 50, fastK, bound_lower]"
    rt = "CCI[1, 14, 50, bound_upper]"
    op = "and"

    AlgoRunner(
        "005790;005930",
        lt,
        rt,
        op
    )