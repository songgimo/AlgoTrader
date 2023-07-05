
class General(object):
    CRYPTO = "Crypto"
    STOCK = "Stock"


class IndicatorName(object):
    GC = "GoldenCross"
    BB = "BollingerBand"
    RSI = "RSI"
    MACD = "MACD"
    STC = "Stochastic"
    CCI = "CCI"


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

