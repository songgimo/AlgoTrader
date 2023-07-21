from PyQt5.QtWidgets import QApplication
from StockApis.Kiwoom.runner import Sender


def sender_test():
    app = QApplication([])
    sd = Sender(
        "005930;066570"
    )

    sd.start()
    app.exec_()


if __name__ == '__main__':
    sender_test()
