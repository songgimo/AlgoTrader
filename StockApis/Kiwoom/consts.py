import os


class TxCode:
    class Get:
        StockInfo = "opt10001"
        AllPrice = "op10004"
        CurrentPrice = "opt10007"
        AccountInfo = "opw00004"
        MarginData = "opw00011"
        BulkFilledData = "opt10055"
        InvestFundVolume = "opt10059"
        DailyCandle = "opt10005"
        DailyChart = "opt10081"

        ExceptDelisting = "1"
        DefaultPasswordType = "00"

    class GetChejan:
        StockCode = "9001"
        StockFilledPrice = "910"
        StockFilledQty = "911"
        OrderNumber = "9203"


class RealReg:
    CurrentPrice = "currentprice"
    Orderbook = "orderbook"


class RequestHeader:
    Trade = "trade"
    Price = "price"
    Common = "common"
    Account = "account"
    TradeInfo = "tradeinfo"


class Etc:
    NoRepeat = 0
    Repeat = 2


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TRADED_SYMBOL_PATH = ROOT_DIR + "/" + "kiwoom_info.json"
