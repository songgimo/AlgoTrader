import threading
import time
import json

from StockApis.Kiwoom import kiwoom, receiver, consts, controllers
from utils import REDIS_SERVER, CONFIG, DEBUG


class AccountRefresher(threading.Thread):
    def __init__(
            self,
            controller: controllers.Controller,
            controller_lock: threading.Lock,
            queue_controller: controllers.QueueController,
    ):
        super().__init__()
        self.setName("AccountRefresher")
        self.account = kiwoom.Account(
            controller,
            controller_lock,
            queue_controller
        )

        self.event = threading.Event()

    def set_ready(self):
        self.event.set()

    def run(self) -> None:
        self.event.wait()
        while True:
            self.account.set_account_info()

            if DEBUG:
                print(self.account.account_info.stock_info, self.account.account_info.cash_balance)

            time.sleep(10)


class Sender(threading.Thread):
    """
        Sender는 TxReceiver와 RealTxThread의 마스터임.

        kiwoom controller를 연결하고
        lock과 queue를 지정하며
        관련 스레드를 실행하고 real reg에 코드를 등록하는 역할을 함.
    """
    def __init__(
            self,
            controller: controllers.Controller,
            controller_lock: threading.Lock,
            queue_controller: controllers.QueueController,
            account_refresher: AccountRefresher,
            code_list: str
    ):
        super().__init__()
        self.setName("SenderThread")
        self.code_list = code_list.split(";")

        self.controller = controller
        self.controller_lock = controller_lock

        self.queue_controller = queue_controller
        self.account_refresher = account_refresher

        self.event = threading.Event()

        self.tx_thread = receiver.TxEventReceiver(
            self.controller,
            self.controller_lock,
            self.queue_controller
        )
        self.real_tx_thread = receiver.RealTxEventReceiver()
        self.chejan_thread = receiver.OnChejanEventReceiver(
            self.controller,
            self.controller_lock,
        )

        self.queue_controller.add("login_queue")
        self.event_thread = receiver.OnEventReceiver(
            self.queue_controller
        )

        self.eager_start_thread()

        self.controller.controller.OnReceiveTrData.connect(self.tx_thread.receive_data)
        self.controller.controller.OnReceiveRealData.connect(self.real_tx_thread.receive_data)
        self.controller.controller.OnEventConnect.connect(self.event_thread.receive_data)
        self.controller.controller.OnReceiveMsg.connect(self.event_thread.receive_message_data)
        self.controller.controller.OnReceiveChejanData.connect(self.chejan_thread.receive_data)

        self.ready_flag = False

    def set_ready(self):
        self.ready_flag = True

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
            self.real_tx_thread,
            self.chejan_thread
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

        self.account_refresher.set_ready()
        self.set_ready()
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

    def real_account_setter(self):
        self.real_account_block = receiver.RealRegBlock(
            self.controller,
            self.controller_lock
        )

        self.real_account_block.define_to_orderbook_block()
        self.real_account_block.init_block_list(
            self.code_list
        )

    def real_operate_time_setter(self):
        self.real_operate_time_block = receiver.RealRegBlock(
            self.controller,
            self.controller_lock
        )

        self.real_operate_time_block.define_to_stock_price_block()
        self.real_operate_time_block.init_block_list(
            self.code_list
        )


class Trader(threading.Thread):
    def __init__(
            self,
            controller: controllers.Controller,
            controller_lock: threading.Lock,
            queue_controller: controllers.QueueController,
            account_object: kiwoom.Account
    ):
        super().__init__()
        self.setName("Trader")
        self.trade_object = kiwoom.Trade(
            controller,
            controller_lock,
            queue_controller,
            account_object
        )
        self._traded_info = {
            "buy": [],
            "sell": []
        }
        self.account_object = account_object

        self.read_traded_info()

    def write_traded_info(self):
        with open(consts.TRADED_SYMBOL_PATH, "w") as file:
            dumps = json.dumps(self._traded_info)
            file.write(dumps)
        REDIS_SERVER.set(consts.RequestHeader.TradeInfo, self._traded_info)

    def read_traded_info(self):
        with open(consts.TRADED_SYMBOL_PATH, "r") as file:
            self._traded_info = json.loads(file.read())

        REDIS_SERVER.set(consts.RequestHeader.TradeInfo, self._traded_info)

    def run(self) -> None:
        while not self.account_object.is_set_account_info():
            print("account-info set 대기 중")
            time.sleep(5)

        print("setting signal 확인.")
        while True:
            signal_data = REDIS_SERVER.pop(consts.RequestHeader.Trade)

            if not signal_data:
                time.sleep(0.1)
                continue

            symbol = signal_data["symbol"]
            price = signal_data["price"]
            trade_type = signal_data["trade_type"]

            if DEBUG:
                print(f"###### signal received, from Trade, {signal_data=} ######")

            if symbol in self._traded_info[trade_type]:
                continue

            self.trade_object.set_symbol(symbol)
            self.trade_object.set_screen_number(symbol[:4])
            self.trade_object.set_trade_price(price)

            self.trade_object.price_code_object.set_market()
            if trade_type == "buy":
                self.trade_object.order_code_object.set_buy()
            else:
                self.trade_object.order_code_object.set_sell()

            self.trade_object.set_quantity()

            self.trade_object.validate()
            result = self.trade_object.execute()

            if result:
                if not DEBUG:
                    self._traded_info[trade_type].append(symbol)
                    self.write_traded_info()

            time.sleep(0.1)
