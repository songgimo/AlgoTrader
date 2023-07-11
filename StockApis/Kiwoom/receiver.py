import threading
import queue

from StockApis.Kiwoom.consts import Etc, RequestHeader, RealReg


class QueueController:
    def __init__(self):
        self.queue_dict = dict()

    def add(self, key):
        self.queue_dict[key] = queue.Queue()

    def remove(self, key):
        del self.queue_dict[key]

    def get(self, key):
        return self.queue_dict[key]

    def put_data(self, key, val):
        self.queue_dict[key].put(val)

    def get_all_keys(self):
        return self.queue_dict.keys()


class RealRegBlock:
    def __init__(self, real_queue_object, controller, controller_lock):
        self.block = dict()

        self.real_queue_object = real_queue_object

        self.controller = controller
        self.controller_lock = controller_lock

        self.real_reg_type = None
        self.fid_code = None
        self.screen_number = ""

    def define_to_current_price_block(self):
        if self.real_reg_type is None:
            self.real_reg_type = RealReg.CurrentPrice
            self.fid_code = "10"
            self.screen_number = "1001"

    def define_to_orderbook_block(self):
        if self.real_reg_type is None:
            self.real_reg_type = RealReg.Orderbook
            self.fid_code = "20"
            self.screen_number = "1002"

    def init_block_list(
            self,
            code_list,
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
                self.real_queue_object.add(stock_code)
                self.block[stock_code] = {
                    stock_code,
                }
    
    def add_to_block(
            self,
            stock_code,
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
    
    def remove_to_block(self, stock_code):
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
    def __init__(self, controller, controller_lock, queue_object):
        super().__init__()
        self._controller = controller
        self._controller_lock = controller_lock
        self._queue_object = queue_object

    def run(self) -> None:
        threading.Event().wait()

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

    def trading_event(self, transaction_code, recode_name):
        return self._controller.get_common_data(transaction_code, recode_name, Etc.NoRepeat, '주문번호')

    def price_event(self, request_name, transaction_code, recode_name):
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
    def __init__(self, controller, controller_lock, real_queue_object_dict):
        super().__init__()
        self.controller = controller
        self.controller_lock = controller_lock

        self.__real_queue_object_dict = real_queue_object_dict

    def receive_data(self, *args):
        try:
            stock_code, real_type, real_data = args
        except:
            return

        if real_type in ["주식시세", "주식체결", "주식예상체결"]:
            real_data = abs(int(real_data.split("\t")[1]))
            queue_object = self.__real_queue_object_dict[RealReg.CurrentPrice]
            queue_object.put_data(stock_code, real_data)

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

            queue_object = self.__real_queue_object_dict[RealReg.Orderbook]
            queue_object.put_data(stock_code, [ask_orderbook, bid_orderbook])

