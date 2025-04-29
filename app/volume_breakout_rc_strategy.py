import backtrader as bt
import pandas as pd
import akshare as ak  # 需安装：pip install akshare


# ==================== 数据获取与预处理（AKShare版本） ====================
def get_akshare_data(stock_code, start_date, end_date):
    """
    使用AKShare获取美股日线数据并处理为backtrader兼容格式
    :param stock_code: 美股代码（如'AAPL'）
    :param start_date: 开始日期（格式'YYYYMMDD'）
    :param end_date: 结束日期（格式'YYYYMMDD'）
    """
    # 获取美股日线数据（前复权）
    stock_data = ak.stock_us_daily(
        symbol=stock_code,
        start_date=start_date,
        end_date=end_date,
        adjust="qfq"  # 前复权处理（消除除权除息影响）
    )
    
    # 重命名列名（backtrader需要'datetime'/'open'/'high'/'low'/'close'/'volume'）
    stock_data.rename(columns={
        "日期": "datetime",
        "开盘价": "open",
        "最高价": "high",
        "最低价": "low",
        "收盘价": "close",
        "成交量": "volume"
    }, inplace=True)
    
    # 转换日期格式并设置为索引
    stock_data['datetime'] = pd.to_datetime(stock_data['datetime'])
    stock_data.set_index('datetime', inplace=True)
    
    # 保留backtrader需要的列（按顺序）
    stock_data = stock_data[['open', 'high', 'low', 'close', 'volume']]
    
    # 保存为CSV（backtrader支持从CSV加载数据）
    stock_data.to_csv(f'{stock_code}.csv')
    return stock_data


# ==================== 策略定义（与原逻辑一致） ====================
class BullStockStrategy(bt.Strategy):
    params = (
        ('breakout_period', 20),   # 突破周期（20日新高）
        ('volume_ratio', 1.5),     # 成交量放大阈值（30日均值的1.5倍）
        ('stop_loss', 0.95),       # 止损比例（5%）
        ('take_profit', 1.20)      # 止盈比例（20%）
    )

    def __init__(self):
        # 计算20日新高（突破线）
        self.high_breakout = bt.indicators.Highest(
            self.data.high, 
            period=self.p.breakout_period
        )
        # 计算30日成交量均线（量能基准）
        self.vol_ma = bt.indicators.SimpleMovingAverage(
            self.data.volume, 
            period=30
        )
        self.order = None  # 记录订单状态

    def next(self):
        # 无持仓时：检查买入信号
        if not self.position:
            # 条件1：收盘价突破20日新高
            # 条件2：当前成交量 > 30日成交量均值 * 放大阈值
            if (self.data.close[0] >= self.high_breakout[0] and 
                self.data.volume[0] > self.vol_ma[0] * self.p.volume_ratio):
                # 全仓买入
                self.order = self.buy()
                # 记录止损价（买入价*0.95）和止盈价（买入价*1.20）
                self.stop_price = self.data.close[0] * self.p.stop_loss
                self.target_price = self.data.close[0] * self.p.take_profit
        else:
            # 持仓时：检查止损/止盈
            if (self.data.close[0] <= self.stop_price or 
                self.data.close[0] >= self.target_price):
                # 平仓（卖出）
                self.sell()


# ==================== 回测配置与运行 ====================
if __name__ == "__main__":
    # 参数设置
    stock_code = 'AAPL'          # 美股代码（苹果）
    start_date = '20200101'      # 开始日期（格式YYYYMMDD）
    end_date = '20240101'        # 结束日期（格式YYYYMMDD）
    
    # 步骤1：使用AKShare获取并处理数据
    data_df = get_akshare_data(stock_code, start_date, end_date)
    
    # 步骤2：初始化backtrader
    cerebro = bt.Cerebro()
    
    # 步骤3：加载数据（从AKShare生成的CSV文件）
    data = bt.feeds.GenericCSVData(
        dataname=f'{stock_code}.csv',
        dtformat=('%Y-%m-%d'),     # 日期格式
        datetime=0,                # 'datetime'列的位置（第0列）
        open=1,                    # 'open'列的位置（第1列）
        high=2,                    # 'high'列的位置（第2列）
        low=3,                     # 'low'列的位置（第3列）
        close=4,                   # 'close'列的位置（第4列）
        volume=5,                  # 'volume'列的位置（第5列）
        openinterest=-1            # 无持仓兴趣数据（-1表示忽略）
    )
    cerebro.adddata(data)
    
    # 步骤4：添加策略
    cerebro.addstrategy(BullStockStrategy)
    
    # 步骤5：配置回测参数
    cerebro.broker.setcash(100000.0)  # 初始资金10万美元
    cerebro.addsizer(bt.sizers.AllInSizer)  # 全仓交易
    
    # 步骤6：运行回测
    print(f"初始资金: {cerebro.broker.getvalue():.2f} 美元")
    cerebro.run()
    print(f"最终资金: {cerebro.broker.getvalue():.2f} 美元")
    
    # 步骤7：可视化（需安装matplotlib）
    cerebro.plot(style='candlestick')