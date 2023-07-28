from PyQt5.QtWidgets import QApplication
from utils import CONFIG
from StockApis.Kiwoom.runner import Sender, Trader
from StockApis.Kiwoom import receiver, objects

import threading


"""
test 확인된 목록
    1. kiwoom api 연동 확인
    2. 복수의 stock_code 입력 확인
    3. real_tx_data receive 확인
    4. QueueController의 get, put

확인 필요 목록
    1. tx data receive 확인
    2. orderbook_price_set 확인 필요
    3. remove to block을 통해 real reg가 삭제가 되는지? 
        -> 삭제가 되는 경우 기존 orderbook 삭제 방안 필요함
    4. redis set/get 최종적으로 확인해 볼 것.


"""


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

    td = Trader(
        ctrl,
        ctrl_lock,
        queue_ctrl,
        CONFIG["kiwoom"]["codes"],
    )

    app.exec_()


if __name__ == '__main__':
    sender_test()
