## 프로젝트의 목적
1. 2개 이상의 보조지표를 통해 주식 시장에서 수익을 일으킨다.

## 프로세스
1. AlgoTrader
   - AlgoTrader는 Redis를 통해 받은 Candle Data를 확인하며 해당 주식 매수/매도 여부를 확인한다.
   - CandleContainer는 각종 candle의 ohlc값과 stock code가 들어감.
   - Stock과 Refresh의 하위 스레드를 가진다.
   - Stock Thread는 인디케이터에 대한 계산과 결과 값을 종합하여 거래 여부에 대한 시그널을 보내는 역할
   - Refresh Thread는 CandleContainer를 지속적으로 핸들링하며 데이터를 가져오고 계산하는 역할
2. StockApis
   - 요청받은 stock/symbol에 대한 candle 데이터와 외부 API(Kiwoom, Sinhan, Binance, Upbit 등)로부터 데이터를 받고 정리하는 StockApis

## 어떻게 진행될 것인가?
1. StockApis의 통신 프로세스는 어디로부터(cfg? AlgoTrader?) 입력받은 주식 코드를 받고 price 값을 받아온다.
2. 이후 Redis를 통해 candle 데이터를 AlgoTrader로 보낸다.
3. Redis를 통해 트리거를  입력받고 해당 데이터에 대한 거래를 진행한다.
4. 이후 데이터 로그를 수집한다(상세 필요함.)


## 매수와 매도 시점
1. 백테스팅을 통한 매수/매도 파라미터를 구하고 테스트한다.


## 지표
1. cross bound lower: 해당 파라미터가 지표 위에 있다가, 아래로 진입했을 경우 매매
2. cross bound upper: 해당 파라미터가 지표 아래 있다가, 위로 진입했을 경우 매매
3. bound upper: 해당 파라미터가 지표 위에 있다면 매매
4. bound lower: 해당 파라미터가 지표 아래에 있다면 매매