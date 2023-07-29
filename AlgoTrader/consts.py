# AlgoTrader 폴더에 사용되는 각종 상수를 선언한 집합


class General(object):
    CRYPTO = "Crypto"
    STOCK = "Stock"


class IndicatorName(object):
    GC = "goldencross"
    BB = "bollingerband"
    RSI = "rsi"
    MACD = "macd"
    STC = "stochastic"
    CCI = "cci"


class OrderingWords(object):
    BL = "BoundLower"
    BU = "BoundUpper"
    CBU = "CrossBoundUpper"
    CBL = "CrossBoundLower"
    AND = "&"
    OR = "|"

    class GC:
        pass

    class STC:
        P_FK = "PreviousFastK"
        P_SD = "PreviousSlowD"
        FK = "FastK"
        SD = "SlowD"

    class MACD:
        HISTOGRAM = "Histogram"
        P_HISTOGRAM = "PreviousHistogram"
        LINE = "Line"
        P_LINE = "PreviousLine"

    class CCI:
        CCI = "CCI"
        P_CCI = "PreviousCCI"

    class RSI:
        RSI = "RSI"
        P_RSI = "PreviousRSI"

