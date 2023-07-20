from StockApis.Kiwoom.runner import Sender


def sender_test():
    sd = Sender(
        "005790;"
    )

    sd.start()

    sd.controller.login()

    sd.join()



if __name__ == '__main__':
    sender_test()