from kiwoom import repository
from kiwoom.port import inbound


def refresh_account_info(account):
    service = repository.AccountRefresherService(
        account
    )

    port_object = inbound.InboundPort()

    port_object.set_account_info_with_account(service)
