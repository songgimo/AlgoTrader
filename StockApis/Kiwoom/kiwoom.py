from StockApis.Kiwoom.consts import RequestHeader, TxCode, Etc
from StockApis.Kiwoom import objects
from utils import CONFIG

import threading


class Account:
    """
        Account 관련 Object
    """

    def __init__(
            self,
            controller: objects.Controller,
            controller_lock: threading.Lock,
            queue_object: objects.QueueController,
    ):
        self.__str = RequestHeader.Account
        self._controller = controller
        self._controller_lock = controller_lock
        self._queue_object = queue_object

        self.account_info = self.AccountInfo(self)
        self.account = CONFIG["kiwoom"]["account"]

        self._set_flag = False

    class AccountInfo:
        def __init__(self, parent):
            self._parent = parent

            self.cash_balance = None
            self.stock_info = None

    def is_set_account_info(self):
        return self._set_flag

    def get_account_list(self):
        return self._controller.get_account_list()

    def get_use_balance_percent(self):
        return int(float(CONFIG["kiwoom"]["use-balance-percent"]) * self.account_info.cash_balance)

    def get_use_stock_percent(self, code):
        result = int(float(CONFIG["kiwoom"]["use-balance-percent"]) * self.account_info.stock_info[code])
        return 1 if result == 0 else result

    def set_account_info(self):
        with self._controller_lock:
            self._controller.set_values('계좌번호', self.account)
            self._controller.set_values('비밀번호', '0000')
            self._controller.set_values('상장폐지조회구분', TxCode.Get.ExceptDelisting)
            self._controller.set_values('비밀번호입력매체구분', TxCode.Get.DefaultPasswordType)

            screen_number = CONFIG["kiwoom"]["account"][:4]
            rq_name = RequestHeader.Account
            self._queue_object.add(rq_name)
            self._controller.request_common_data(rq_name, TxCode.Get.AccountInfo, Etc.NoRepeat, screen_number)

        stock_queue = self._queue_object.get(rq_name)
        try:
            remaining_info = stock_queue.get(True, timeout=10)
        except Exception as ex:
            print(ex)
            return
        self.account_info.cash_balance = remaining_info["cash_balance"]
        self.account_info.stock_info = remaining_info["stock_balance"]

        self._set_flag = True

class SetPriceCode:
    """
        외부로부터 trading_code를 입력받아
    """
    def __init__(self):
        self.trading_code = None
        self.trading_str = ""

    def set_limit(self):
        self.trading_code, self.trading_str = ("00", "limit")

    def set_market(self):
        self.trading_code, self.trading_str = ("03", "market")


class SetOrderCode:
    def __init__(self):
        self.order_code = None
        self.order_str = ""

    def set_buy(self):
        self.order_code, self.order_str = (1, "buy")

    def set_sell(self):
        self.order_code, self.order_str = (2, "sell")

    def set_cancel_buy(self):
        self.order_code, self.order_str = (3, "cancelbuy")

    def set_cancel_sell(self):
        self.order_code, self.order_str = (4, "cancelsell")

    def set_change_buy(self):
        self.order_code, self.order_str = (5, "changebuy")

    def set_change_sell(self):
        self.order_code, self.order_str = (6, "changesell")


class Trade:
    """
        하나의 Trade Object는 하나의 stock_code를 담당한다.
    """
    def __init__(
            self,
            controller: objects.Controller,
            controller_lock: threading.Lock,
            queue_controller: objects.QueueController,
            account_object: Account
    ):
        self.__str = RequestHeader.Trade
        self._controller = controller
        self._controller_lock = controller_lock
        self._queue_object = queue_controller
        self._stock_code = None
        self._qty = None
        self._price = None

        self.order_code_object = SetOrderCode()
        self.price_code_object = SetPriceCode()
        self.account_object = account_object

        self._screen_number = None
        self._validate_check = False
        self._request_name = None
        self._origin_order_number = ""

    def validate(self) -> bool:
        if self.order_code_object.order_code is None:
            # raise trade type error
            raise "order code가 없음."
        elif self.price_code_object is None:
            raise "price code가 존재하지 않음."
        elif self._price is None:
            raise "price 값이 설정되어야 합니다."
        elif self._qty is None:
            raise "quantity 값이 설정되어야 합니다."
        elif self._screen_number is None:
            raise "screen number 값이 설정되어야 합니다."

        self._validate_check = True
        return True

    def set_origin_order_number(self, number):
        self._origin_order_number = number

    def set_symbol(self, code):
        self._stock_code = code

    def set_request_name(self):
        self._request_name = "_".join([
            self.__str,
            self._stock_code,
            self.order_code_object.order_str,
            self.price_code_object.trading_str
        ])

    def set_screen_number(self, number):
        self._screen_number = number

    def set_trade_price(self, price: str):
        self._price = int(price)

    def set_quantity(self):
        if self.order_code_object.order_str == "buy":
            use_balance = self.account_object.get_use_balance_percent()
            self._qty = use_balance // self._price
        elif self.order_code_object.order_str == "sell":
            self._qty = self.account_object.get_use_stock_percent(self._stock_code)

    def execute(self):
        if not self._validate_check:
            raise "validate check가 우선되어야 합니다."

        if not self._request_name:
            self.set_request_name()
            self._queue_object.add(self._request_name)

        if self.price_code_object.trading_code == "03":
            self._price = 0

        order_parameters = [
            self._request_name,
            self._screen_number,
            self.account_object.account,
            self.order_code_object.order_code,
            self._stock_code,
            self._qty,
            self._price,
            self.price_code_object.trading_code,
            self._origin_order_number
        ]

        with self._controller_lock:
            self._controller.send_order(*order_parameters)

        trade_queue = self._queue_object.get(self._request_name)
        try:
            order_number = trade_queue.get(True, timeout=10)
            return order_number
        except:
            return 0


class Common:
    """
        별도의 queue를 통한 통신이 필요없는 값들은, Common object에 들어가며 호출된다.
    """
    def __init__(self, controller, queue_object):
        self.__str = RequestHeader.Common
        self._controller = controller
        self._queue_object = queue_object

    def get_kospi_stock_codes(self):
        ret = self._controller.dynamicCall("GetCodeListByMarket(QString)", ["0"])
        return ret.split(';')

    def get_kosdaq_stock_codes(self):
        ret = self._controller.dynamicCall("GetCodeListByMarket(QString)", ["10"])
        return ret.split(';')

    def get_stock_codes(self):
        kospi = self.get_kospi_stock_codes()
        kosdaq = self.get_kosdaq_stock_codes()
        return dict(kospi=kospi, kosdaq=kosdaq)


class Price:
    """
        하나의 Price Object는 하나의 stock_code를 담당한다.
    """
    def __init__(
            self,
            controller: objects.Controller,
            controller_lock: threading.Lock,
            queue_object: objects.QueueController,
            stock_code
    ):
        self.__str = RequestHeader.Price
        self._controller = controller
        self._controller_lock = controller_lock
        self._queue_object = queue_object
        self._stock_code = stock_code

        self._request_name = None

    def set_request_name(self, item_name):
        self._request_name = "_".join([
            self.__str,
            self._stock_code,
            item_name
        ])

    def get_stock_history(self, item_name):
        screen_number = self._stock_code[:4]

        self.set_request_name(item_name)
        with self._controller_lock:
            self._controller.set_values('종목코드', self._stock_code)
            self._queue_object.add(self._request_name)
            self._controller.request_common_data(self._request_name, TxCode.Get.DailyCandle, Etc.NoRepeat, screen_number)

        stock_queue = self._queue_object.get(self._request_name)
        data = stock_queue.get(True, timeout=10)
        print(data)

        return data

    def get_stock_information(self, item_name):
        screen_number = self._stock_code

        self.set_request_name(item_name)

        self._controller.set_values('종목코드', self._stock_code)
        self._queue_object.add(self._request_name)
        self._controller.request_common_data(self._request_name, TxCode.Get.CurrentPrice, Etc.NoRepeat, screen_number)

        stock_queue = self._queue_object.get(self._request_name)
        data = stock_queue.get(True, timeout=10)
        print(data)

        return data

    def get_current_price(self):
        return self.get_stock_information(item_name='현재가')

    def get_highest_price(self):
        return self.get_stock_information(item_name='상한가')

    def get_opening_price(self):
        return self.get_stock_information(item_name='시가')

    def get_stock_history_data(self):
        return self.get_stock_history(item_name="stock-history")
