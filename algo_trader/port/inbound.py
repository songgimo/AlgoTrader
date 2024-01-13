from algo_trader import repository
from algo_trader.port import outbound


class ThreadInboundPort:
    def __init__(self):
        self._kiwoom_api_port = outbound.KiwoomAPIPort()
        self._redis_port = outbound.RedisPort()

    def calculate_golden_cross_and_bollinger_band(
            self,
            primary: repository.GoldenCross,
            secondary: repository.BollingerBand
    ):

        primary_data = primary.calculator(self._kiwoom_api_port)
        secondary_data = secondary.calculator(self._kiwoom_api_port)

        result = primary.check_values(primary_data) and secondary.check_values(secondary_data)

        if result:
            trade_result = self._redis_port.set_buy_trigger(
                primary.get_name(),
                secondary.get_name()
            )
        else:
            trade_result = False

        return trade_result

