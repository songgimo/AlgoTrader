import threading

from StockApis.Kiwoom import kiwoom, receiver, consts


if __name__ == '__main__':
    ctrl = kiwoom.Controller()
    ctrl_lock = threading.Lock()
    q_ctrl = receiver.QueueController()
    real_queue_dict = {
        consts.RealReg.CurrentPrice: receiver.QueueController(),
        consts.RealReg.Orderbook: receiver.QueueController()
    }

    tx_thread = receiver.TxEventReceiver(ctrl, ctrl_lock, q_ctrl)
    real_tx_thread = receiver.RealTxEventReceiver(ctrl, ctrl_lock, real_queue_dict)
    tx_thread.run()

    common_object = kiwoom.Common(ctrl, q_ctrl)

    stock_code_dict = common_object.get_stock_codes()

    price_object = kiwoom.Price(ctrl, q_ctrl, stock_code_dict["kosdaq"][-1])
    price_object.get_current_price()
