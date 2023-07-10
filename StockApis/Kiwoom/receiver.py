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

    def receive_tx_data(self, *args):
        try:
            scn_no, rq_name, tx_code, rc_name, repeat, d_len, err_code, msg, sp_msg = args
        except Exception as ex:
            raise ex

        identifier = rq_name.split("_")[0]

        with self._controller_lock:
            if RequestHeader.Trade == identifier:
                result = self.trading_event(tx_code, rc_name)
            elif RequestHeader.Price == identifier:
                result = self.price_event(rq_name, tx_code, rc_name)

            self._queue_object.put_data(rq_name, result)

    def trading_event(self, tx_code, rc_name):
        return self._controller.get_common_data(tx_code, rc_name, Etc.NoRepeat, '주문번호')

    def price_event(self, rq_name, tx_code, rc_name):
        identifier, stock_codes, item_name = rq_name.split('_')
        if item_name == "대량종목명":
            dict_ = dict()
            code_list = stock_codes.split(';')
            for i in range(self._get_repeat_count(tx_code, rq_name)):
                res = self.get_common_data_with_repeat(tx_code, rq_name, i, '종목명')
                dict_.update({code_list[i]: res})
            return dict_

        return self._controller.get_common_data(tx_code, rc_name, Etc.NoRepeat, item_name)
