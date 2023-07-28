from PyQt5.QAxContainer import QAxWidget
import queue


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


class Controller:
    """
        KHOpenAPICtrl과 연결하기 위해 하나의 Controller object를 각 object들이 공유하는 형태이며,
        각 object들은 lock으로 접근을 제한한다.
    """
    def __init__(self):
        self.controller = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.controller.dynamicCall("CommConnect()")
        # self.controller = client.Dispatch("KHOPENAPI.KHOpenAPICtrl.1")

    def send_order(
            self,
            request_name,
            screen_number,
            account,
            order_type,
            stock_code,
            quantity,
            price,
            trade_type,
            origin_order_number
    ):
        wrap = [
            request_name,
            screen_number,
            account,
            order_type,
            stock_code,
            quantity,
            price,
            trade_type,
            origin_order_number
        ]

        self.controller.dynamicCall(
            'SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)',
            wrap
        )

    def get_common_data(
            self,
            transaction_code,
            recode_name,
            index,
            item_name
    ):
        # transaction_code, recode_name, index, item_name
        # return tx_data for getting signal
        wrap = [
            transaction_code,
            recode_name,
            index,
            item_name
        ]
        return self.controller.dynamicCall(
            'GetCommData(QString, QString, int, QString)',
            wrap
        )

    def get_common_data_with_repeat(
            self,
            transaction_code,
            request_name,
            index,
            item_name
    ):
        wrap = [
            transaction_code,
            request_name,
            index,
            item_name
        ]
        return self.controller.dynamicCall(
            'GetCommData(QString, QString, int, QString)',
            wrap
        )

    def get_repeat_count(self, transaction_code, request_name):
        wrap = [
            transaction_code,
            request_name
        ]
        return self.controller.dynamicCall(
            'GetRepeatCnt(QString, QString)',
            wrap
        )

    def get_common_real_data(self, stock_code, real_type):
        wrap = [
            stock_code,
            real_type
        ]
        return self.controller.dynamicCall(
            'GetCommRealData(QString, int)',
            wrap
        )

    def set_values(self, name, value):
        wrap = [
            name,
            value
        ]
        return self.controller.dynamicCall(
            'SetInputValue(QString, QString)',
            wrap
        )

    def request_common_data(
            self,
            request_name,
            transaction_code,
            repeat,
            screen_number
    ):
        wrap = [
            request_name,
            transaction_code,
            repeat,
            screen_number
        ]
        # request to KiwoomAPI and return result.
        return self.controller.dynamicCall(
            'commRqData(QString, QString, int, QString)',
            wrap
        )

    def set_real_reg(
            self,
            screen_number,
            code_list,
            fid_list,
            real_type
    ):
        wrap = [
            screen_number,
            code_list,
            fid_list,
            real_type
        ]

        return self.controller.dynamicCall(
            'SetRealReg(QString, QString, QString, QString)',
            wrap
        )

    def remove_real_reg(self, screen_number, stock_code):
        wrap = [
            screen_number, stock_code
        ]

        return self.controller.dynamicCall(
            'SetRealRemove(QString, QString)',
            wrap
        )
