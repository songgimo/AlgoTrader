class KiwoomAPIPort:
    def __init__(self):
        super().__init__()

    def get_close_candles_by_period(self, period: int):
        pass

    def get_yesterday_close_candles_by_period(self, period: int):
        pass


class RedisPort:
    def __init__(self):
        super().__init__()

    def set_buy_trigger(
            self,
            primary_indicator_name: str,
            secondary_indicator_name: str
    ):
        pass

    def set_sell_trigger(
            self,
            primary_indicator_name: str,
            secondary_indicator_name: str
    ):
        pass
