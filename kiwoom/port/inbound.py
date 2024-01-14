from kiwoom import repository
from kiwoom.port import outbound


class InboundPort:
    def __init__(self):
        super().__init__()

        self._kiwoom_api_port = outbound.KiwoomAPIPort()

    def set_account_info_with_account(
            self,
            service: repository.AccountRefresherService
    ):
        service.set_account_info(self._kiwoom_api_port)
