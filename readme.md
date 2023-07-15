## 프로젝트의 목적
1. 2개 이상의 보조지표를 통해 주식 시장에서 수익을 일으킨다.

## 프로세스
1. Redis를 통해 candle 데이터를 입력받고 거래 트리거를 발생시키는 AlgoTrader
2. 요청받은 stock/symbol에 대한 candle 데이터와 외부 API(Kiwoom, Sinhan, Binance, Upbit 등)로부터 데이터를 받고 정리하는 StockApis


## 어떻게 진행될 것인가?
1. StockApis의 통신 프로세스는 어디로부터(cfg? AlgoTrader?) 입력받은 주식 코드를 받고 price 값을 받아온다.
2. 이후 Redis를 통해 candle 데이터를 AlgoTrader로 보낸다.
3. Redis를 통해 트리거를 입력받고 해당 데이터에 대한 거래를 진행한다.
4. 이후 데이터 로그를 수집한다(상세 필요함.)


## 매수와 매도 시점
1. 백테스팅을 통한 매수/매도 파라미터를 구하고 테스트한다.
