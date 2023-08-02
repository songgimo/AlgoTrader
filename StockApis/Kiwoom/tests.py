from PyQt5.QtWidgets import QApplication
from utils import CONFIG
from StockApis.Kiwoom.runner import Sender, Trader
from StockApis.Kiwoom import receiver, objects

import threading


def sender_test():
    app = QApplication([])

    ctrl = objects.Controller()
    ctrl_lock = threading.Lock()

    queue_ctrl = objects.QueueController()

    sd = Sender(
        ctrl,
        ctrl_lock,
        queue_ctrl,
        CONFIG["kiwoom"]["codes"],
    )

    sd.start()

    for _ in range(2):
        td = Trader(
            ctrl,
            ctrl_lock,
            queue_ctrl,
        )

        td.start()

    app.exec_()


if __name__ == '__main__':
    sender_test()
