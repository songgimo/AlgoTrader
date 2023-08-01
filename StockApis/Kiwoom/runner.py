import threading
import time
import atexit

from StockApis.Kiwoom import kiwoom, receiver, consts, objects
from utils import REDIS_SERVER, CONFIG, DEBUG


class Sender(threading.Thread):
    """
        Sender는 TxReceiver와 RealTxThread의 마스터임.

        kiwoom controller를 연결하고
        lock과 queue를 지정하며
        관련 스레드를 실행하고 real reg에 코드를 등록하는 역할을 함.
    """
    def __init__(
            self,
            controller: objects.Controller,
            controller_lock: threading.Lock,
            queue_controller: objects.QueueController,
            code_list: str
    ):
        super().__init__()
        self.code_list = code_list.split(";")

        self.controller = controller
        self.controller_lock = controller_lock

        self.queue_controller = queue_controller

        self.event = threading.Event()

        self.tx_thread = receiver.TxEventReceiver(
            self.controller,
            self.controller_lock,
            self.queue_controller
        )
        self.real_tx_thread = receiver.RealTxEventReceiver()

        self.queue_controller.add("login_queue")
        self.event_thread = receiver.OnEventReceiver(
            self.queue_controller
        )

        self.eager_start_thread()

        self.controller.controller.OnReceiveTrData.connect(self.tx_thread.receive_data)
        self.controller.controller.OnReceiveRealData.connect(self.real_tx_thread.receive_data)
        self.controller.controller.OnEventConnect.connect(self.event_thread.receive_data)

    def eager_start_thread(self):
        threads = [
            self.event_thread
        ]

        for thread in threads:
            thread.start()
            time.sleep(1)

    def run(self):
        threads = [
            self.tx_thread,
            self.real_tx_thread
        ]

        for thread in threads:
            thread.start()
            time.sleep(0.1)

        while True:
            # wait to connect KiwoomAPI
            queue = self.queue_controller.get("login_queue")
            try:
                data = queue.get(timeout=10)
                break
            except:
                print("로그인 대기 중입니다.")
            time.sleep(1)
        print("로그인 완료.")

        self.real_current_price_setter()
        history_data = dict()
        for code in self.code_list:
            price_object = kiwoom.Price(
                self.controller,
                self.controller_lock,
                self.queue_controller,
                code
            )
            result = price_object.get_stock_history_data()
            history_data.update(result)

        REDIS_SERVER.set(consts.RequestHeader.Price, history_data)
        self.event.wait()

    def real_current_price_setter(self):
        self.real_current_price_block = receiver.RealRegBlock(
            self.controller,
            self.controller_lock,
        )

        self.real_current_price_block.define_to_stock_price_block()
        self.real_current_price_block.init_block_list(
            self.code_list
        )

    def real_orderbook_setter(self):
        self.real_orderbook_block = receiver.RealRegBlock(
            self.controller,
            self.controller_lock,
        )

        self.real_orderbook_block.define_to_orderbook_block()
        self.real_orderbook_block.init_block_list(
            self.code_list
        )


class Trader(threading.Thread):
    def __init__(
            self,
            controller: objects.Controller,
            controller_lock: threading.Lock,
            queue_controller: objects.QueueController,
            stock_code: str,
    ):
        super().__init__()
        self.trade_object = kiwoom.Trade(
            controller,
            controller_lock,
            queue_controller,
            stock_code,
        )

        self.define_trade_object()

    def define_trade_object(self):
        self.trade_object.price_code_object.set_market()
        if CONFIG["kiwoom"]["trade-type"] == "buy":
            self.trade_object.order_code_object.set_buy()
        else:
            self.trade_object.order_code_object.set_sell()

        self.trade_object.set_request_name()

        self.trade_object.validate()
        self.trade_object.set_screen_number("0101")

    def run(self) -> None:
        while True:
            signal = REDIS_SERVER.get(consts.RequestHeader.Trade)

            if signal is None:
                continue

            if DEBUG:
                print(f"###### signal received, from Trade, {signal=} ######")
            # self.trade_object.execute()


def delete_kiwoom_data():
    try:
        keys = [
            consts.RealReg.CurrentPrice,
            consts.RealReg.Orderbook
        ]
        REDIS_SERVER.delete(keys)
    except:
        print("fail to delete kiwoom data")


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication
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

    atexit.register(delete_kiwoom_data)

    sd.start()

    td = Trader(
        ctrl,
        ctrl_lock,
        queue_ctrl,
        CONFIG["kiwoom"]["codes"],

    )

    app.exec_()
