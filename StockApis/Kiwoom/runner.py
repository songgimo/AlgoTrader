import threading

from StockApis.Kiwoom import controllers, communicators
from utils import REDIS_SERVER, CONFIG, DEBUG
from PyQt5.QtWidgets import QApplication


class Runner:
    def __init__(self):
        self._controller = controllers.Controller()
        self._controller_lock = threading.Lock()
        self._queue_controller = controllers.QueueController()

        self._account_refresher = communicators.AccountRefresher(
            self._controller,
            self._controller_lock,
            self._queue_controller,
        )

        self._sender = communicators.Sender(
            self._controller,
            self._controller_lock,
            self._queue_controller,
            self._account_refresher,
            CONFIG["kiwoom"]["codes"]
        )

        self._trader = communicators.Trader(
            self._controller,
            self._controller_lock,
            self._queue_controller,
            self._account_refresher.account
        )

    def start_communicators(self):
        REDIS_SERVER.flush_all()

        self._sender.start()
        self._account_refresher.start()
        self._trader.start()


if __name__ == '__main__':
    app = QApplication([])

    app.exec_()
