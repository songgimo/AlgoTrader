import re

import numpy as np
import consts
import indicators


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
        if consts.IndicatorName.GC in name:
            return indicators.GoldenCross(indicate_data, self._exchange)

        elif consts.IndicatorName.BB in name:
            return indicators.BollingerBand(indicate_data, self._exchange)

        elif consts.IndicatorName.RSI in name:
            return indicators.RelativeStrengthIndex(indicate_data, self._exchange)

        elif consts.IndicatorName.MACD in name:
            return indicators.MACD(indicate_data, self._exchange)

        elif consts.IndicatorName.STC in name:
            return indicators.Stochastic(indicate_data, self._exchange)

        elif consts.IndicatorName.CCI in name:
            return indicators.CCI(indicate_data, self._exchange)



class BaseAlgorithm(object):
    def __init__(self, indicate_data, exchange, calculator_type):
        self._settings = dict()
        self._exchange = exchange
        self._calculator_type = calculator_type
        self.calculator = self.get_calculator()
        self.base_settings(indicate_data)
        self.indicator_settings(indicate_data)

    def base_settings(self, indicate_data):
        self._settings.update({
            "candle_size": indicate_data[0],
            "trade_method": indicate_data[-1]
        })

    def get_calculator(self):
        if self._calculator_type == General.CRYPTO:
            return self.calculate_by_crypto
        else:
            return self.calculate_by_stock

    def indicator_settings(self, indicate_data):
        pass

    def check_values(self):
        return

    def update_settings(self, **kwargs):
        self._settings.update(**kwargs)

    def calculate_by_crypto(self):
        pass

    def calculate_by_stock(self):
        pass

    def is_suitable_trading(self):
        return True if self.check_values() else False

    def get_sma(self, values: list) -> int:
        return np.average(values)



"""
    Packing - unpacking에 발생하는 slippage 고민
    지속적으로 변하는 indicator에 대한 부하와 속도
    exchange 대신 Redis PubSub 데이터
    
    과정
    1. 각 Indicator tree wrapping
    2. 과정에서 Redis PubSub을 받을 수 있는 pipe parameter
    3. pub이 발생한 경우 trigger, object 내부에서 데이터 변화
    4. 지속적 감시 채널에서 데이터 확인 및 거래
    
    BaseAlgorithm -> Stock, Crypto 로의 추상화 분리
    
    CCI, Stochastic등은 인터페이스로 처리해서 완전히 다르도록 처리
    
    TODO
    키움, 신한I, 코인 거래소 등 Candle을 가져오고 계산할 수 있는 general calculate 함수 개발 필요.
"""