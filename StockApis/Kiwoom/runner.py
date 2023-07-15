import threading
from StockApis.Kiwoom import kiwoom, receiver


class Sender:
    """
        Sender는 TxReceiver와 RealTxThread의 마스터임.

        kiwoom controller를 연결하고
        lock과 queue를 지정하며
        관련 스레드를 실행하고 real reg에 코드를 등록하는 역할을 함.
    """
    def __init__(self, code_list):
        self.code_list = code_list

        self.controller = kiwoom.Controller()
        self.controller_lock = threading.Lock()

        self.queue_controller = receiver.QueueController()

        self.tx_thread = receiver.TxEventReceiver(
            self.controller,
            self.controller_lock,
            self.queue_controller
        )
        self.real_tx_thread = receiver.RealTxEventReceiver()

        self.tx_thread.run()
        self.real_tx_thread.run()

        self.real_current_price_setter()
        self.real_orderbook_setter()

    def run(self):
        while True:
            pass

    def real_current_price_setter(self):
        self.real_current_price_block = receiver.RealRegBlock(
            self.controller,
            self.controller_lock,
        )

        self.real_current_price_block.define_to_current_price_block()
        self.real_current_price_block.init_block_list(
            self.code_list
        )

    def real_orderbook_setter(self):
        self.real_orderbook_block = receiver.RealRegBlock(
            self.controller,
            self.controller_lock,
        )

        self.real_orderbook_block.define_to_current_price_block()
        self.real_orderbook_block.init_block_list(
            self.code_list
        )
