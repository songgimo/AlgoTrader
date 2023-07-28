from StockApis.Kiwoom.consts import Etc, RequestHeader, RealReg
from utils import REDIS_SERVER

import threading
import queue

from StockApis.Kiwoom import objects


class QueueController:
    def __init__(self):
        self.queue_dict = dict()

    def add(self, key: str):
        self.queue_dict[key] = queue.Queue()

    def remove(self, key: str):
        del self.queue_dict[key]

    def get(self, key: str):
        return self.queue_dict[key]

    def put_data(self, key: str, val: str):
        self.queue_dict[key].put(val)

    def get_all_keys(self):
        return self.queue_dict.keys()


class RealRegBlock:
    """
        RealReg의 등록 및 삭제를 원활하게 하기 위한 Object
    """
    def __init__(
            self,
            controller: objects.Controller,
            controller_lock: threading.Lock,
    ):
        self.block = dict()

        self.controller = controller
        self.controller_lock = controller_lock

        self.real_reg_type = None
        self.fid_code = None
        self.screen_number = ""

    def define_to_stock_price_block(self):
        close = "10"
        open_ = "16"
        high = "17"
        low = "18"

        if self.real_reg_type is None:
            self.real_reg_type = RealReg.CurrentPrice
            self.fid_code = ";".join([close, open_, high, low])
            self.screen_number = "1001"

    def define_to_orderbook_block(self):
        if self.real_reg_type is None:
            self.real_reg_type = RealReg.Orderbook
            self.fid_code = "20"
            self.screen_number = "1002"

    def init_block_list(
            self,
            code_list: list,
    ):
        with self.controller_lock:
            result = self.controller.set_real_reg(
                self.screen_number,
                ";".join(code_list),
                self.fid_code,
                "0"
            )

        if result:
            for stock_code in code_list:
                self.block[stock_code] = {
                    stock_code,
                }
    
    def add_to_block(
            self,
            stock_code: str,
    ):
        if stock_code in self.get_registered_stock_code_list():
            return

        with self.controller_lock:
            result = self.controller.set_real_reg(
                self.screen_number,
                stock_code,
                self.fid_code,
                "1"
            )
        if result:
            self.block[stock_code] = {
                stock_code,
            }
    
    def remove_to_block(self, stock_code: str):
        if stock_code not in self.get_registered_stock_code_list():
            return

        with self.controller_lock:
            result = self.controller.remove_real_reg(
                self.screen_number,
                stock_code
            )

        if result:
            del self.block[stock_code]

    def get_registered_stock_code_list(self):
        return self.block.keys()

    
class TxEventReceiver(threading.Thread):
    """
        제시된 dynamic call에 대해 결과 값을 받는 event receiver
        request_name으로 어떠한 정보들로부터 call 받았는지 확인할 수 있다.
    """
    def __init__(
            self,
            controller: objects.Controller,
            controller_lock: threading.Lock,
            queue_object: QueueController
    ):
        super().__init__()
        self._controller = controller
        self._controller_lock = controller_lock
        self._queue_object = queue_object
        self.daemon = True
        self.event = threading.Event()

    def run(self) -> None:
        self.event.wait()

    def receive_data(self, *args):
        try:
            (
                screen_number,
                request_name,
                transaction_code,
                recode_name,
                repeat,
                d_len,
                error_code,
                message,
                special_message
            ) = args
        except Exception as ex:
            raise ex
        
        identifier = request_name.split("_")[0]

        with self._controller_lock:
            if RequestHeader.Trade == identifier:
                result = self.trading_event(transaction_code, recode_name)
            elif RequestHeader.Price == identifier:
                result = self.price_event(request_name, transaction_code, recode_name)

            self._queue_object.put_data(request_name, result)

    def trading_event(self, transaction_code: int, recode_name: str):
        return self._controller.get_common_data(transaction_code, recode_name, Etc.NoRepeat, '주문번호')

    def price_event(
            self,
            request_name: str,
            transaction_code: int,
            recode_name: str
    ):
        identifier, stock_codes, item_name = request_name.split('_')
        if item_name == "대량종목명":
            dict_ = dict()
            code_list = stock_codes.split(';')
            for i in range(self._controller.get_repeat_count(transaction_code, request_name)):
                res = self._controller.get_common_data_with_repeat(transaction_code, request_name, i, '종목명')
                dict_.update({code_list[i]: res})
            return dict_

        return self._controller.get_common_data(transaction_code, recode_name, Etc.NoRepeat, item_name)


class RealTxEventReceiver(threading.Thread):
    """
        체결같은 지속적으로 데이터를 Publish받고 싶을 때 사용하는 클래스
        dynamic call을 통해 RealReg를 등록하고 이후 이벤트 발생 시 해당 함수의 receive_data로 hooking된다.

        해당 event는 빈번하게 발생하므로, redis로 연결하여 데이터를 지속적으로 갱신한다.
    """
    def __init__(
            self,
    ):
        super().__init__()
        self.daemon = True

        self.current_price_dict = dict()
        self.orderbook_price_dict = dict()

        self.event = threading.Event()

    def run(self) -> None:
        self.event.wait()

    def receive_data(self, *args) -> None:
        try:
            stock_code, real_type, real_data = args
        except:
            return

        if real_type in ["주식시세", "주식체결", "주식예상체결"]:
            real_data = abs(int(real_data.split("\t")[1]))
            if stock_code not in self.current_price_dict:
                self.current_price_dict[stock_code] = [real_data]
            else:
                if len(self.current_price_dict[stock_code]) > 100:
                    self.current_price_dict[stock_code] = self.current_price_dict[stock_code][1:]
                self.current_price_dict[stock_code].append(real_data)
            REDIS_SERVER.set(RealReg.CurrentPrice, self.current_price_dict)

        elif real_type == "주식호가잔량":
            real_data = real_data.split('\t')
            ask_orderbook = {
                real_data[i]: real_data[i + 1]
                for i in range(55, 0, -6)
            }
            bid_orderbook = {
                real_data[i]: real_data[i + 1]
                for i in range(4, 59, 6)
            }

            if stock_code not in self.orderbook_price_dict:
                self.orderbook_price_dict[stock_code] = [ask_orderbook, bid_orderbook]
            else:
                if len(self.orderbook_price_dict[stock_code]) > 100:
                    self.orderbook_price_dict[stock_code] = self.orderbook_price_dict.pop(0)
                self.orderbook_price_dict[stock_code].append(real_data)

            REDIS_SERVER.set(RealReg.Orderbook, self.orderbook_price_dict)


class OnEventReceiver(threading.Thread):
    def __init__(self, queue_controller: QueueController):
        super().__init__()
        self.daemon = True
        self._queue_controller = queue_controller
        self.event = threading.Event()

    def run(self) -> None:
        self.event.wait()

    def receive_data(self, code):
        if code == 0:
            self._queue_controller.put_data("login_queue", "T")
