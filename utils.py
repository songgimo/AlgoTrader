import redis
import json
import configparser
import sys
from decimal import Decimal, getcontext, InvalidOperation


DEBUG = True if 'pydevd' in sys.modules else False

getcontext().prec = 8


class RedisController:
    def __init__(self):
        self._server = redis.Redis(host="127.0.0.1", port=25100)

    def get(self, key: str, use_decimal=False):
        try:
            value = self._server.get(key)

            if not value:
                return None

            if use_decimal:
                json_to_dict_value = json.loads(value, cls=DecimalDecoder)
            else:
                json_to_dict_value = json.loads(value)

            return json_to_dict_value
        except:
            return None

    def set(self, key: str, value: str):
        result = self._server.set(key, json.dumps(value))
        return result

    def delete(self, keys: list):
        self._server.delete(*keys)


class DecimalDecoder(json.JSONDecoder):
    """
        total_data에 대한 데이터 값은 그대로 있어야 함
        end_line인 경우 string or float, int
        들어올 때 타입확인,
        [3, 4, 6, [3, 4, 7, [6,5,3,3]]]
    """
    def decode_converter(self, type_, tc, dic=False):
        for k in tc:
            if isinstance(k, list):
                type_.append(list())
                self.decode_converter(type_[-1], k)
            elif isinstance(k, dict):
                type_.append(dict())
                self.decode_converter(type_[-1], k, True)
            else:
                if dic:
                    if isinstance(tc[k], list):
                        type_[k] = list()
                        self.decode_converter(type_[k], tc[k])
                    elif isinstance(tc[k], dict):
                        type_[k] = dict()
                        self.decode_converter(type_[k], tc[k], True)
                    else:
                        if isinstance(tc[k], (float, int, str)):
                            try:
                                type_[k] = Decimal(tc[k])
                            except InvalidOperation:
                                type_[k] = tc[k]
                        else:
                            type_[k] = tc[k]
                else:
                    if isinstance(k, (float, int, str)):
                        try:
                            type_.append(Decimal(k))
                        except InvalidOperation:
                            type_.append(k)
                    else:
                        type_.append(k)

    def decode(self, s, _w=None):
        decoded = json.JSONDecoder.decode(self, s)
        if isinstance(decoded, dict):
            decode_with_decimal = dict()
            is_dic = True
        else:
            decode_with_decimal = list()
            is_dic = False
        self.decode_converter(decode_with_decimal, decoded, is_dic)

        return decode_with_decimal


REDIS_SERVER = RedisController()

CONFIG = configparser.ConfigParser()
CONFIG.read('./settings.ini')
