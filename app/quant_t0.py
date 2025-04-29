import pandas as pd
import numpy as np
from scipy import stats
import akshare as ak


# ==================== 数据获取（个股+板块，AKShare版本） ====================
def get_market_data(stock_code, index_code, start_date, end_date, freq='1'):
    """
    获取个股与对应板块指数的分钟级数据（AKShare版本）
    :param stock_code: 个股代码（如'sz000001'）
    :param index_code: 板块指数代码（如'sh000001'代表上证指数，需选AKShare支持的指数）
    :param freq: 分钟频率（"1"=1分钟，"5"=5分钟等）
    """
    # 获取个股分钟数据（示例：平安银行，代码sz000001）
    stock_data = ak.stock_zh_a_hist_min_em(
        symbol=stock_code,
        period=freq,
        # start_date=start_date.replace('-', ''),
        # end_date=end_date.replace('-', ''),
        adjust="qfq"  # 前复权处理
    )
    stock_data['datetime'] = pd.to_datetime(stock_data['date'])
    stock_data.set_index('datetime', inplace=True)
    stock_data = stock_data[['close', 'volume']]  # 保留收盘价和成交量
    
    # 获取板块指数分钟数据（示例：新能源车指数，需确认AKShare是否支持该指数）
    # 注：AKShare部分指数无分钟数据，可替换为日线数据或选择支持的指数（如上证指数sh000001）
    index_data = ak.index_zh_a_minute(
        symbol=index_code,
        period=freq,
        start_date=start_date.replace('-', ''),
        end_date=end_date.replace('-', ''),
        adjust=""  # 指数一般无需复权
    )
    index_data['datetime'] = pd.to_datetime(index_data['date'])
    index_data.set_index('datetime', inplace=True)
    index_data = index_data[['close', 'volume']].rename(columns={
        'close': 'index_close',
        'volume': 'index_volume'
    })
    
    # 合并个股与板块数据（按时间对齐，仅保留共同时间戳）
    merged_data = pd.merge(
        stock_data,
        index_data,
        left_index=True,
        right_index=True,
        how='inner'
    )
    return merged_data


# ==================== 板块联动指标计算（与原逻辑一致） ====================
def calculate_indicators(data):
    """计算个股+板块的联动指标"""
    # 个股指标
    data['ma5'] = data['close'].rolling(5).mean()          # 个股5分钟均线
    data['ma30'] = data['close'].rolling(30).mean()        # 个股30分钟均线
    data['atr'] = data['close'].rolling(30).apply(lambda x: max(x) - min(x))  # 个股30分钟波动范围
    
    # 板块指标
    data['index_ma5'] = data['index_close'].rolling(5).mean()  # 板块5分钟均线
    data['index_ma30'] = data['index_close'].rolling(30).mean()# 板块30分钟均线
    data['index_pct'] = data['index_close'].pct_change()       # 板块分钟涨跌幅
    data['index_vol_boost'] = data['index_volume'] > 1.5 * data['index_volume'].rolling(30).mean()  # 板块放量信号
    
    # 个股-板块相关性（30分钟滚动）
    data['corr'] = data[['close', 'index_close']].rolling(30).corr().iloc[:, 0]  # 皮尔逊相关系数
    
    # 相对强度（个股涨跌幅 - 板块涨跌幅）
    data['rs'] = data['close'].pct_change() - data['index_pct']
    
    # 时间特征（过滤开盘/收盘时段）
    data['time'] = data.index.time
    return data


# ==================== 板块联动信号生成（与原逻辑一致） ====================
def generate_signals(data, corr_threshold=0.7):
    """生成买卖信号（1=买入，-1=卖出，0=无操作）"""
    data['signal'] = 0
    
    # 基础条件：时间+波动率+相关性
    time_mask = (data['time'] >= pd.Timestamp('09:30:00').time()) & (data['time'] <= pd.Timestamp('14:00:00').time())
    vol_mask = data['atr'] > 0.3  # 个股波动率阈值（可根据股票调整）
    corr_mask = data['corr'] > corr_threshold  # 个股与板块强相关
    
    # 板块趋势判断
    index_up = data['index_ma5'] > data['index_ma30']  # 板块均线金叉（上升趋势）
    index_down = data['index_ma5'] < data['index_ma30'] # 板块均线死叉（下降趋势）
    
    # 板块资金与一致性（示例用放量代替）
    index_strong = index_up & data['index_vol_boost']   # 板块强势（上升+放量）
    index_weak = index_down & data['index_vol_boost']   # 板块弱势（下降+放量）
    
    # 个股信号（均线交叉）
    stock_gold = (data['ma5'] > data['ma30']) & (data['ma5'].shift(1) <= data['ma30'].shift(1))  # 个股金叉
    stock_death = (data['ma5'] < data['ma30']) & (data['ma5'].shift(1) >= data['ma30'].shift(1)) # 个股死叉
    
    # 联动信号规则
    data.loc[stock_gold & time_mask & vol_mask & corr_mask & index_strong, 'signal'] = 1  # 板块强势+个股金叉→买入
    data.loc[stock_death & time_mask & vol_mask & corr_mask & index_weak, 'signal'] = -1  # 板块弱势+个股死叉→卖出
    
    return data


# ==================== 交易执行（与原策略一致） ====================
def execute_trades(data, base_position=1000, max_day_trade=500, fee=0.001):
    """模拟交易执行（保留原仓位管理逻辑）"""
    # （代码与原策略一致，此处省略，可参考之前的完整实现）
    return data


# ==================== 主函数 ====================
def main():
    # 参数设置（AKShare代码格式示例）
    stock_code = 'sz000001'    # 个股代码（平安银行，AKShare格式为sz+代码）
    index_code = 'sh000001'    # 板块指数（上证指数，AKShare支持的指数代码）
    start_date = '2025-01-01'
    end_date = '2025-01-31'
    
    # 步骤1：获取个股+板块数据（AKShare版本）
    try:
        data = get_market_data(stock_code, index_code, start_date, end_date, freq='1')
    except Exception as e:
        print(f"数据获取失败：{e}，请检查指数代码是否在AKShare支持范围内（如替换为sh000001）")
        return
    
    # 步骤2：计算联动指标
    data = calculate_indicators(data)
    
    # 步骤3：生成联动信号
    data = generate_signals(data, corr_threshold=0.7)
    
    # 输出关键信号验证
    print("触发买入信号的时刻：")
    print(data[data['signal'] == 1].index)
    print("\n触发卖出信号的时刻：")
    print(data[data['signal'] == -1].index)

if __name__ == "__main__":
    main()