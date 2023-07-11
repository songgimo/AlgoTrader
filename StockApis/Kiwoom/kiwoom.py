from StockApis.Kiwoom.consts import TradingCode, RequestHeader, TxCode
import re


class AccountInfo:
    """
        account 관련 정보 추가
    """
    def __init__(self):
        self.account_number = None

    def set_account_number(self, account_number):
        self.account_number = account_number


class SetPriceCode:
    def __init__(self):
        self.trading_code = None
        self.trading_str = ""

    def set_limit(self):
        self.trading_code, self.trading_str = TradingCode.LimitPrice

    def set_market(self):
        self.trading_code, self.trading_str = TradingCode.MarketPrice


class SetOrderCode:
    def __init__(self):
        self.order_code = None
        self.order_str = ""

    def set_buy(self):
        self.order_code, self.order_str = TradingCode.Buy

    def set_sell(self):
        self.order_code, self.order_str = TradingCode.Sell

    def set_cancel_buy(self):
        self.order_code, self.order_str = TradingCode.CancelBuy

    def set_cancel_sell(self):
        self.order_code, self.order_str = TradingCode.CancelSell

    def set_change_buy(self):
        self.order_code, self.order_str = TradingCode.ChangeBuy

    def set_change_sell(self):
        self.order_code, self.order_str = TradingCode.ChangeSell


class Trade:
    def __init__(self, controller, queue_object, stock_code, qty, price):
        self.__str = RequestHeader.Trade
        self._controller = controller
        self._queue_object = queue_object
        self._stock_code = stock_code
        self._qty = qty
        self._price = price

        self.order_code_object = SetOrderCode()
        self.price_code_object = SetPriceCode()
        self.account_object = AccountInfo()

        self._screen_number = stock_code
        self._validate_check = False
        self._rq_name = None
        self._origin_order_number = ""

    def validate(self):
        if self.order_code_object.order_code is None:
            # raise trade type error
            return "order code가 없음."
        elif self.price_code_object is None:
            return "price code가 존재하지 않음."

        self._validate_check = True
        return "정상적인 데이터"

    def set_origin_order_number(self, number):
        self._origin_order_number = number

    def set_rq_name(self):
        self._rq_name = "_".join([
            self.__str,
            self._stock_code,
            self.order_code_object.order_str,
            self.price_code_object.trading_str
        ])

    def set_screen_number(self, number):
        self._screen_number = number

    def execute(self):
        if not self._validate_check:
            raise "validate check가 우선되어야 합니다."

        if not self._rq_name:
            self.set_rq_name()
            self._queue_object.add(self._rq_name)

        order_parameters = [
            self._rq_name,
            self._screen_number,
            self.account_object.account_number,
            self.order_code_object.order_code,
            self._stock_code,
            self._qty,
            self._price,
            self.price_code_object.trading_code,
            self._origin_order_number
        ]

        self._controller.send_order(*order_parameters)

        trade_queue = self._queue_object.get(self._rq_name)

        order_number = trade_queue.get(True, timeout=10)

        return order_number


class Common:
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
    def __init__(self, controller, queue_object, stock_code):
        self.__str = RequestHeader.Price
        self._controller = controller
        self._queue_object = queue_object
        self._stock_code = stock_code

        self._rq_name = None

    def set_rq_name(self, item_name):
        self._rq_name = "_".join([
            self.__str,
            self._stock_code,
            item_name
        ])

    def get_stock_information(self, item_name):
        screen_number = self._stock_code

        self.set_rq_name(item_name)

        self._controller.set_values('종목코드', self._stock_code)
        self._queue_object.add(self._rq_name)
        self._controller.request_common_data(self._rq_name, TxCode.Get.StockInfo, screen_number)

        stock_queue = self._queue_object.get(self._rq_name)
        raw_price = stock_queue.get(True, timeout=10)
        price = int(re.sub(r'[^\d]', '', raw_price))

        return price

    def get_current_price(self):
        return self.get_stock_information(item_name='현재가')

    def get_highest_price(self):
        return self.get_stock_information(item_name='상한가')

    def get_opening_price(self):
        return self.get_stock_information(item_name='시가')


class Controller:
    def __init__(self):
        self._controller = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")

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

        self._controller.dynamicCall(
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
        return self._controller.dynamicCall(
            'GetCommData(QString, QString, int, QString)',
            wrap
        )

    def get_common_data_with_repeat(self, common_parameters: list):
        # transaction_code, rq_name, index, item_name
        return self._controller.dynamicCall(
            'GetCommData(QString, QString, int, QString)',
            common_parameters
        )

    def get_repeat_count(self, transaction_code, rq_name):
        return self._controller.dynamicCall('GetRepeatCnt(QString, QString)', [transaction_code, rq_name])

    def get_common_real_data(self, stock_code, real_type):
        return self._controller.dynamicCall(
            'GetCommRealData(QString, int)',
            [stock_code, real_type]
        )

    def set_values(self, name, value):
        return self._controller.dynamicCall(
            'SetInputValue(QString, QString)',
            name,
            value
        )

    def request_common_data(self, common_parameters: list):
        # name, transaction_code, repeat, screen_num
        # request to KiwoomAPI and return result.
        return self._controller.dynamicCall(
            'commRqData(QString, QString, int, QString)',
            common_parameters
        )

    def _set_real_reg(self, screen_number, code_list, fid_list, real_type):
        self._controller.dynamicCall('SetRealReg(QString, QString, QString, QString)',
                                     [screen_number, code_list, fid_list, real_type])
