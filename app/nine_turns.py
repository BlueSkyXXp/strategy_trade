# -*- coding: utf-8 -*-
import akshare as ak
import pandas as pd
from datetime import datetime


# 神奇九转核心算法
def calculate_nine_turns(df):
    """计算九转序列"""
    df['up_condition'] = df['close'] > df['close'].shift(4)
    df['down_condition'] = df['close'] < df['close'].shift(4)

    # 连续计数逻辑
    for condition in ['up', 'down']:
        streak = 0
        streaks = []
        for idx in range(len(df)):
            if df[f'{condition}_condition'].iloc[idx]:
                streak = streak + 1 if streak < 9 else 9
            else:
                streak = 0
            streaks.append(streak)
        df[f'{condition}_streak'] = streaks

    # 生成买卖信号
    df['ma20'] = df['close'].rolling(20).mean()
    # df['buy_signal'] = (df['down_streak'] == 9) & (df['close'] > df['ma20'])
    df['buy_signal'] = (df['down_streak'] == 9)
    # df['sell_signal'] = (df['up_streak'] == 9) & (df['close'] < df['ma20'])
    df['sell_signal'] = (df['up_streak'] == 9)
    return df


# 数据获取
def get_stock_data(symbol, start, end):
    """获取A股前复权数据"""
    try:
        code = f"{symbol}"
        df = ak.stock_zh_a_hist(
            symbol=code, period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="qfq"
        )
        df = df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close',
            '最高': 'high', '最低': 'low', '成交量': 'volume'
        })
        df['date'] = pd.to_datetime(df['date'])
        return df.set_index('date').sort_index()
    except Exception as e:
        print(f"数据获取失败：{str(e)}")
        return None


# 示例调用
if __name__ == "__main__":
    symbol = "300548"

    stock_zh_a_hist_min_em_df = ak.stock_zh_a_hist_min_em(symbol="300548", start_date="2025-05-09 09:30:00",
                                                          end_date="2025-05-09 15:00:00", period="5", adjust="")
    print(stock_zh_a_hist_min_em_df)
    start_date = datetime(2024, 10, 8)
    end_date = datetime.now()
    data = get_stock_data(symbol, start_date, end_date)
    if data is not None:
        analyzed_data = calculate_nine_turns(data)
        print(analyzed_data)



