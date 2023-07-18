import redis
import json
from decimal import Decimal, getcontext, InvalidOperation
getcontext().prec = 8


REDIS_SERVER = redis.Redis(host="localhost", port=6379)


def get_redis(key, use_decimal=False):
    try:
        value = REDIS_SERVER.get(key)

        if not value:
            return None

        if use_decimal:
            json_to_dict_value = json.loads(value, cls=DecimalDecoder)
        else:
            json_to_dict_value = json.loads(value)

        return json_to_dict_value
    except:
        return None


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
