from backup.StockApis.Kiwoom.consts import Etc, RequestHeader, RealReg
from utils import REDIS_SERVER

import threading
import re

from StockApis.Kiwoom import controllers


class RealRegBlock:
    """
        RealReg의 등록 및 삭제를 원활하게 하기 위한 Object
    """
    def __init__(
            self,
            controller: controllers.Controller,
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
            self.screen_number = "0001"

    def define_to_orderbook_block(self):
        if self.real_reg_type is None:
            self.real_reg_type = RealReg.Orderbook
            self.fid_code = "20"
            self.screen_number = "0002"

    def define_to_account_block(self):
        close = "10"
        amount = "930"
        buy_price = "931"

        if self.real_reg_type is None:
            self.real_reg_type = RealReg.Account
            self.fid_code = ";".join([close, amount, buy_price])
            self.screen_number = "0003"

    def define_start_market_time_block(self):
        trade_time = "20"
        remain_time = "214"
        operate_check = "215"

        if self.real_reg_type is None:
            self.real_reg_type = RealReg.OperateTime
            self.fid_code = ";".join([trade_time, remain_time, operate_check])
            self.screen_number = "0004"

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
            controller: controllers.Controller,
            controller_lock: threading.Lock,
            queue_object: controllers.QueueController
    ):
        super().__init__()
        self.setName("TxEventReceiver")
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
            elif RequestHeader.Account == identifier:
                result = self.account_event(request_name, transaction_code, recode_name)
            self._queue_object.put_data(request_name, result)

    def trading_event(self, transaction_code: int, recode_name: str):
        return self._controller.get_common_data(transaction_code, recode_name, Etc.NoRepeat, '주문번호')

    def account_event(
            self,
            request_name: str,
            transaction_code: int,
            recode_name: str
    ):
        data = {}
        cash_balance = self._controller.get_common_data(transaction_code, recode_name, Etc.NoRepeat, '예수금')
        data['cash_balance'] = int(re.sub(r'[^\d]', '', cash_balance))
        data['stock_balance'] = dict()
        code_list = []
        stock_prices = []
        for i in range(self._controller.get_repeat_count(transaction_code, request_name)):
            code = self._controller.get_common_data_with_repeat(transaction_code, request_name, i, '종목코드')
            current_stock = self._controller.get_common_data_with_repeat(transaction_code, request_name, i, '보유수량')
            code_list.append(code)
            stock_prices.append(int(current_stock))

        replace = re.findall("\d+", ";".join(code_list))

        data['stock_balance'] = {key: val for key, val in zip(replace, stock_prices)}

        return data

    def price_event(
            self,
            request_name: str,
            transaction_code: int,
            recode_name: str
    ):
        identifier, stock_code, item_name = request_name.split('_')
        if item_name == "stock-history":
            result = []
            for i in range(self._controller.get_repeat_count(transaction_code, request_name)):
                list_ = [
                    self._controller.get_common_data_with_repeat(transaction_code, request_name, i, '날짜').strip(),
                    self._controller.get_common_data_with_repeat(transaction_code, request_name, i, '시가').strip(),
                    self._controller.get_common_data_with_repeat(transaction_code, request_name, i, '저가').strip(),
                    self._controller.get_common_data_with_repeat(transaction_code, request_name, i, '고가').strip(),
                    self._controller.get_common_data_with_repeat(transaction_code, request_name, i, '종가').strip()
                ]
                result.append(list_)

            return {stock_code: result}

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
        self.setName("RealTxEventReceiver")
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
        print(real_type, real_data)
        if real_type in ["주식시세", "주식체결"]:
            real_data = real_data.split("\t")
            close = abs(int(real_data[1]))
            open_ = abs(int(real_data[9]))
            high = abs(int(real_data[10]))
            low = abs(int(real_data[11]))

            if stock_code not in self.current_price_dict:
                self.current_price_dict[stock_code] = {
                    "candles": [close],
                }
            else:
                if len(self.current_price_dict[stock_code]) > 100:
                    self.current_price_dict[stock_code] = self.current_price_dict[stock_code][1:]
                self.current_price_dict[stock_code]["candles"].append(real_data)

            self.current_price_dict[stock_code].update({
                "close": close,
                "open": open_,
                "high": high,
                "low": low
            })
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
        elif real_type == "잔고":
            print(real_data)


class OnEventReceiver(threading.Thread):
    def __init__(self, queue_controller: controllers.QueueController):
        super().__init__()
        self.setName("OnEventReceiver")
        self.daemon = True
        self._queue_controller = queue_controller
        self.event = threading.Event()

    def run(self) -> None:
        self.event.wait()

    def receive_data(self, code):
        if code == 0:
            self._queue_controller.put_data("login_queue", "T")

    def receive_message_data(self, *args):
        print(f"get message, {args}")


class OnChejanEventReceiver(threading.Thread):
    def __init__(
            self,
            controller: controllers.Controller,
            controller_lock: threading.Lock,
    ):
        super().__init__()
        self.setName("OnEventReceiver")
        self._controller = controller
        self._controller_lock = controller_lock
        self.daemon = True
        self.event = threading.Event()

    def run(self) -> None:
        self.event.wait()

    def receive_data(self, *args):
        code, real_type, real_data = args
        print(args)
        with self._controller_lock:
            fid_list = real_data.split(';')
            for each in fid_list:
                self._controller.get_chejan_data(each)
