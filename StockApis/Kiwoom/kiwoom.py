from StockApis.Kiwoom.consts import TradingCode


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
    def __init__(self, controller, stock_code, qty, price):
        self._controller = controller
        self._stock_code = stock_code
        self._qty = qty
        self._price = price

        self.order_code_object = SetOrderCode()
        self.price_code_object = SetPriceCode()
        self.account_object = AccountInfo()

        self._validate_check = False
        self._rq_name = None

    def validate(self):
        if self.order_code_object.order_code is None:
            # raise trade type error
            return "order code가 없음."
        elif self.price_code_object is None:
            return "price code가 존재하지 않음."

        self._validate_check = True
        return "정상적인 데이터"

    def set_rq_name(self):
        self._rq_name = "_".join([
            self._stock_code,
            self.order_code_object.order_str,
            self.price_code_object.trading_str
        ])

    def execute(self):
        if not self._validate_check:
            raise "validate check가 우선되어야 합니다."

        if not self._rq_name:
            self.set_rq_name()

        info = [
            self._rq_name,
            self.account_object.account_number,
            self.order_code_object.order_code,
            self._stock_code,
            self._qty,
            self._price,
            self.price_code_object.trading_code,
        ]
