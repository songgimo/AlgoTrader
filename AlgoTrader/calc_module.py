import re

import numpy as np


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


class IndicatorTree(object):
    def unpack_string_contents(self, contents):
        def unpack(c):
            if c.startswith("(") and c.endswith(")"):
                c = c[1:-1]

            return c

        cnt = 0
        for n, content in enumerate(contents):
            if content == "&" and not cnt:
                return "&", unpack(contents[:n]), unpack(contents[n+1:])
            elif content == "|" and not cnt:
                return "|", unpack(contents[:n]), unpack(contents[n+1:])
            elif content == "(":
                cnt += 1
            elif content == ")":
                cnt -= 1

        return contents

    def build_node(self, contents):
        if contents is None:
            return None
        val, left, right = self.unpack_string_contents(contents)

        return IndicatorNode(val, self.build_node(left), self.build_node(right), self._exchange)


class IndicatorNode(object):
    def __init__(self, val, left, right, exchange):
        self.left = self.convert_string(left)
        self.right = self.convert_string(right)
        self.val = val
        self._exchange = exchange

    def convert_string(self, data):
        if data is None:
            return None

        elif data.val in {"&", "|"}:
            return data

        data = re.findall("[\d\w]+", data.val.lower())

        name, indicate_data = data[0], data[1:]
        if IndicatorName.GC in name:
            return GoldenCross(indicate_data, self._exchange)

        elif IndicatorName.BB in name:
            return BollingerBand(indicate_data, self._exchange)

        elif IndicatorName.RSI in name:
            return RelativeStrengthIndex(indicate_data, self._exchange)

        elif IndicatorName.MACD in name:
            return MACD(indicate_data, self._exchange)

        elif IndicatorName.STC in name:
            return Stochastic(indicate_data, self._exchange)

        elif IndicatorName.CCI in name:
            return CCI(indicate_data, self._exchange)


class BaseAlgorithm(object):
    def __init__(self, indicate_data, exchange):
        self._settings = dict()
        self._exchange = exchange
        self.base_settings(indicate_data)
        self.indicator_settings(indicate_data)

    def base_settings(self, indicate_data):
        self._settings.update({
            "candle_size": indicate_data[0],
            "trade_method": indicate_data[-1]
        })

    def indicator_settings(self, indicate_data):
        pass

    def get_sma(self, values: list) -> int:
        return np.average(values)


class GoldenCross(BaseAlgorithm):
    def __init__(self, indicate_data, exchange):
        super().__init__(indicate_data, exchange)


class BollingerBand(BaseAlgorithm):
    def __init__(self, indicate_data, exchange):
        super().__init__(indicate_data, exchange)

    def indicator_settings(self, indicate_data):
        self._settings.update({
            "period": int(indicate_data[1]),
            "deviation": int(indicate_data[2]),
            "reference": indicate_data[3]
        })


class RelativeStrengthIndex(BaseAlgorithm):
    def __init__(self, indicate_data, exchange):
        super().__init__(indicate_data, exchange)

    def indicator_settings(self, indicate_data):
        self._settings.update({
            "period": int(indicate_data[1]),
            "bound": int(indicate_data[2])
        })


class MACD(BaseAlgorithm):
    def __init__(self, indicate_data, exchange):
        super().__init__(indicate_data, exchange)

    def indicator_settings(self, indicate_data):
        self._settings.update({
            "short_period": int(indicate_data[1]),
            "long_period": int(indicate_data[2]),
            "signal_period": int(indicate_data[3]),
            "bound": int(indicate_data[4]),
            "reference": indicate_data[5]
        })


class Stochastic(BaseAlgorithm):
    def __init__(self, indicate_data, exchange):
        super().__init__(indicate_data, exchange)


class CCI(BaseAlgorithm):
    def __init__(self, indicate_data, exchange):
        super().__init__(indicate_data, exchange)



"""
    Packing - unpacking에 발생하는 slippage 고민
    지속적으로 변하는 indicator에 대한 부하와 속도
    exchange 대신 Redis PubSub 데이터
    
    과정
    1. 각 Indicator tree wrapping
    2. 과정에서 Redis PubSub을 받을 수 있는 pipe parameter
    3. pub이 발생한 경우 trigger, object 내부에서 데이터 변화
    4. 지속적 감시 채널에서 데이터 확인 및 거래
    
    
    TODO
    키움, 신한I, 코인 거래소 등 Candle을 가져오고 계산할 수 있는 general calculate 함수 개발 필요.
"""