import threading
import queue

from StockApis.Kiwoom.consts import Etc, RequestHeader


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
            for i in range(self._get_repeat_count(transaction_code, request_name)):
                res = self.get_common_data_with_repeat(transaction_code, request_name, i, '종목명')
                dict_.update({code_list[i]: res})
            return dict_

        return self._controller.get_common_data(transaction_code, recode_name, Etc.NoRepeat, item_name)


class RealTxEventReceiver(threading.Thread):
    def __init__(self, controller, controller_lock, queue_object):
        super().__init__()

    def receive_data(self, *args):
        try:
            code, real_type, real_data = args
        except:
            pass

    def registry_real_current_price_data(self, stock_code_list):
        for code in stock_code_list:
            self._real_service_q.setdefault('current_price', {code: list()})

        stock_code_list = ';'.join(stock_code_list)
        return self._set_real_reg(screen_number=REAL_CURRENT_PRICE_SCREEN_NUM,
                                  code_list=stock_code_list,
                                  fid_list=CURRENT_PRICE_CODE,
                                  real_type=ONLY_LAST_REGISTRY)
