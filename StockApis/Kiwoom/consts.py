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

    class GetChejan:
        StockCode = "9001"
        StockFilledPrice = "910"
        StockFilledQty = "911"
        OrderNumber = "9203"


class TradingCode:
    Buy = (1, "buy")
    Sell = (2, "sell")
    CancelBuy = (3, "cancelbuy")
    CancelSell = (4, "cancelsell")
    ChangeBuy = (5, "changebuy")
    ChangeSell = (6, "changesell")

    LimitPrice = ("00", "limit")
    MarketPrice = ("03", "market")


class SetRealRegit:
    """
        이벤트 통신을 위한 실시간 체결 관련 코드
    """
    OnlyLastRegit = "0"
    AddRegit = "1"
    CurrentPrice = "10"
    FilledDate = "20"
    TradeAmount = "15"

