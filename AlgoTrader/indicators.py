"""
    각종 indicator 지표들의 집합 파일
    각 indicator들의 상태는 어떤 exchange type이냐에 따라 변화한다.

    현재로는 crypto-stock 두 개의 지표 거래만 지원한다.
"""
import consts
import numpy as np


class AbstractIndicator:
    pass


class AbstractStock:
    """
        stock class의 Abstract model
        Crpyto와 함수가 다를 수 있으므로 분리
    """
    def __init__(self, settings, exchange):
        self.__settings = settings
        self.__exchange = exchange


class AbstractCrypto:
    """
        crypto class의 Abstract model
        Stok와 함수가 다를 수 있으므로 분리
    """

    def __init__(self, settings, exchange):
        self.__exchange = exchange
        self.__settings = settings

    def get_sma(self, value):
        sma = np.sum(value) / len(value)

        return sma


class GoldenCross:

    class Stock(AbstractStock):
        def calculate(self):
            pass

    class Crypto(AbstractCrypto):
        def calculate(self, symbol):
            suc, candles, msg = self.__exchange.get_candle(
                symbol,
                self.__settings['candle_size'],
                self.__settings['long_period'] + 1
            )

            if not suc:
                return suc, candles, msg

            short_close = candles['close'][:self.__settings['short_period']]
            long_close = candles['close'][:self.__settings['long_period']]

            prev_short_close = candles['close'][1:self.__settings['short_period'] + 1]
            prev_long_close = candles['close'][:self.__settings['long_period'] + 1]

            prev_short_sma = self.get_sma(prev_short_close)
            prev_long_sma = self.get_sma(prev_long_close)

            short_sma = self.get_sma(short_close)
            long_sma = self.get_sma(long_close)

            res = {
                'short_sma': short_sma,
                'long_sma': long_sma,
                'prev_short_sma': prev_short_sma,
                'prev_long_sma': prev_long_sma
            }

            return True, res, ''

        def check_values(self, values):
            if values['prev_short_sma'] >= values['prev_long_sma']:
                if values['prev_short_sma'] >= values['prev_long_sma']:
                    return True
                else:
                    return False
            else:
                return False

    def __init__(self, settings, exchange):
        if exchange == consts.General.STOCK:
            self._executor = self.Stock(exchange, settings)

        elif exchange == consts.General.CRYPTO:
            self._executor = self.Crypto(exchange, settings)

    def calculator(self, symbol):
        """
            거래소 간 발생한 에러들에 대해 처리 및 상위 로직으로 반환
        """
        success, data, message = self._executor.calculate(symbol)
        
        if success:
            result = self._executor.check_values(data)
        
        else:
            # 에러를 어떻게 처리할 것인지?
            result = False
        
        return result


class BollingerBand:
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


