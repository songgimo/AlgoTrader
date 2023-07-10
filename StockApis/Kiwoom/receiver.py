import threading
import queue


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
    def __init__(self, controller, queue_object):
        super().__init__()
        self._controller = controller
        self._queue_object = queue_object

    def run(self) -> None:
        threading.Event().wait()

    def get_common_data(self, tx_code, rc_name, index, item_name):
        # return tx_data for getting signal
        return self._controller.dynamicCall('GetCommData(QString, QString, int, QString)',
                                            [tx_code, rc_name, index, item_name]).replace(' ', '')

    def receive_tx_data(self, *args):
        try:
            scn_no, rq_name, tx_code, rc_name, repeat, d_len, err_code, msg, sp_msg = args
        except Exception as ex:
            raise ex

        data_queue = self._queue_object.put_data(rq_name, "")


