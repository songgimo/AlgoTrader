from StockApis.Kiwoom.runner import Sender


def sender_test():
    sd = Sender(
        "005790;"
    )

    sd.set_receivers()
    sd.real_current_price_setter()
    sd.real_orderbook_setter()
    # sd.join()


if __name__ == '__main__':
    sender_test()