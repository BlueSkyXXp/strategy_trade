import logging
from datetime import datetime

from app.core import trade_service
from app.core.stock_service import StockService
import pandas as pd
from app.core.stock_cache import StockCache
from app.core.log_config import setup_logger
import akshare as ak

logger = setup_logger(__name__)

stock_api = StockService()
trade_api = trade_service.TradeService()

def run_job(cache_manager):
    logger.info("开始交易-----")
    trading_calendar = cache_manager.get_trading_calendar()
    if trading_calendar.empty:
        trading_calendar = stock_api.is_trade_date(date=datetime.now().strftime('%Y-%m-%d'))
        cache_manager.update_trading_calendar()
    if  trading_calendar.empty:
        logger.info("非交易日，不执行策略")
        return
    if datetime.now().strftime('%Y-%m-%d') not in trading_calendar['jyrq'].values:
        logger.info("非交易日，不执行策略")
        return
    
    now_time = datetime.now().time()
    if not stock_api.is_trade_time(now_time):
        logger.info("非交易时间，不执行策略")
        return
    logger.info("交易日，执行策略")
    # 如果超过10点半，则不执行策略
    now = datetime.now()
    if now.hour > 10 or (now.hour == 10 and now.minute >= 30):
        logger.info("超过10点半,不执行策略")
        return

    logger.info("在交易时间，执行策略")
    # 从缓存中加载昨日涨停股票池、持仓和余额信息
    yesterday_limit_up_stocks, position, balance = cache_manager.load_stocks_from_cache()

    dt_limit_up_stocks = cache_manager.get_yesterday_limit_down_stocks()


    board_concept_df = stock_api.get_board_concept_stock_top_ten()
    if board_concept_df is None or not isinstance(board_concept_df, pd.DataFrame) or board_concept_df.empty:
        logger.error("未能获取有效的板块概念股票前十数据，跳过后续处理")
        return
    # 每个板块获取前10只股票
    board_concept_stocks_df = pd.DataFrame()
    for _, row in board_concept_df.iterrows():
        # 今日如果某个板块已经买过2只股票，则这个板块就不买了
        if cache_manager.get_today_buy_board_id(row['f12']) >= 2:
            continue
        temp_df = stock_api.get_board_concept_stock_cons_top_twenty(row['f12'])
        # 添加板块id列
        temp_df['board_id'] = row['f12']
        board_concept_stocks_df = pd.concat([board_concept_stocks_df, temp_df], ignore_index=True)
    board_concept_stocks_df = board_concept_stocks_df.drop_duplicates(subset='f12')
    # 排除昨日涨停的股票池, 首板
    board_concept_stocks_df = board_concept_stocks_df[~board_concept_stocks_df['f12'].isin(yesterday_limit_up_stocks['c'])]
    # 排除跌停的股票池
    board_concept_stocks_df = board_concept_stocks_df[~board_concept_stocks_df['f12'].isin(dt_limit_up_stocks['c'])]

    # 排除退市的票 ST * 退
    board_concept_stocks_df = board_concept_stocks_df[~board_concept_stocks_df['f14'].str.contains('ST')]
    board_concept_stocks_df = board_concept_stocks_df[~board_concept_stocks_df['f14'].str.contains('*', regex=False)]
    board_concept_stocks_df = board_concept_stocks_df[~board_concept_stocks_df['f14'].str.contains('退')]

    # 保留流通市值10-30亿之间 或者200亿以上  f21是流通市值
    board_concept_stocks_df = board_concept_stocks_df[((board_concept_stocks_df['f21'] >= 100000000) & (board_concept_stocks_df['f21'] <= 300000000)) | (board_concept_stocks_df['f21'] >= 2000000000)]

    # 排除科创板688开头 
    board_concept_stocks_df = board_concept_stocks_df[~board_concept_stocks_df['f12'].str.startswith('688')]

    # 主板（60或者00开头）涨幅大于等于9.5%， 创业板（30开头）涨幅大于等于19.5%     f12是股票代码
    board_concept_stocks_df['f3'] = pd.to_numeric(board_concept_stocks_df['f3'], errors='coerce')
    board_concept_stocks_df = board_concept_stocks_df.dropna(subset=['f3'])
    
    main_board_condition = (board_concept_stocks_df['f12'].str.startswith('60') | board_concept_stocks_df['f12'].str.startswith('00')) & (board_concept_stocks_df['f3'] >= 950)
    gem_condition = (board_concept_stocks_df['f12'].str.startswith('30')) & (board_concept_stocks_df['f3'] >= 1950)
    board_concept_stocks_df = board_concept_stocks_df[main_board_condition | gem_condition]
    
    # 获取涨幅榜 上证前50只+深圳前50只
    stock_gain_df = pd.DataFrame(stock_api.get_stock_sh_zs_rank())
    stock_gain_df = pd.concat([stock_gain_df, pd.DataFrame(stock_api.get_stock_sz_zs_rank())])

    # 获取涨速榜 上证前10只+深圳前10只
    stock_speed_df = pd.DataFrame(stock_api.get_stock_sh_zs_speed_rank())
    stock_speed_df = pd.concat([stock_speed_df, pd.DataFrame(stock_api.get_stock_sz_zs_speed_rank())])

    # 三个数据集取交集，以股票代码为基准
    board_concept_stocks_df = pd.merge(board_concept_stocks_df, stock_gain_df, on='f12', how='inner')
    board_concept_stocks_df = pd.merge(board_concept_stocks_df, stock_speed_df, on='f12', how='inner')

    # 排除今日已经买进的股票
    board_concept_stocks_df = board_concept_stocks_df[~board_concept_stocks_df['f12'].isin(cache_manager.get_today_buy_stocks())]



    if board_concept_stocks_df.empty:
        logger.info("没有符合条件的股票")
        return
    else:
        logger.info("符合条件的股票：%s", board_concept_stocks_df)
    # 买入board_concept_stocks_df中的股票,每个股票买一万。
    for _, row in board_concept_stocks_df.iterrows():
        stock_code = row['f12']
        bid_df = stock_api.stock_bid_ask_em(symbol=stock_code)
        # 确保 zt_price 是一个有效的数值
        if 'f51' in bid_df.columns:
            zt_price = bid_df['f51'].values[0] if len(bid_df['f51'].values) > 0 else 0
        else:
            logger.warning(f"未能获取股票 {stock_code} 的涨停价格，跳过买入")
            continue
        # 1万元，以涨停价买入，买入数量为100及其整数倍
        if zt_price > 0:
            # 修改此处，确保 buy_num 是 100 的整数倍
            buy_num = (int(10000 / zt_price) // 100) * 100
            buy_resp = trade_api.buy_stock(stock_code=stock_code,price=zt_price, amount=buy_num)
            if buy_resp and buy_resp.get('code') == 0:
                logger.info("买入成功，股票代码：%s,买入数量：%s,买入价格:%s", stock_code, buy_num, zt_price)
                balance = balance - buy_num * zt_price
                cache_manager.set_balance(balance)
                cache_manager.append_today_buy_stock(stock_code)
                cache_manager.append_today_buy_board_id(row['board_id'])
                logger.info("今天买入的股票池：%s", cache_manager.get_today_buy_stocks())         
            else:
                logger.error("买入失败，股票代码：%s,买入数量：%s,买入价格:%s", stock_code, buy_num, zt_price)
        else:
            logger.warning(f"股票 {stock_code} 的涨停价格为 0，跳过买入")
        # cache_manager.update_cache()

if __name__ == "__main__":
    stock_a_df = ak.stock_zh_a_hist(symbol='002734', period='daily', start_date='20250401', end_date='20250430')
    # 重命名列名以匹配分析需求
    stock_a_df = stock_a_df.rename(columns={
        "日期": "date",
        "开盘": "open",
        "收盘": "close",
        "最高": "high",
        "最低": "low",
        "成交量": "volume"
    })
    stock_a_df['date'] = pd.to_datetime(stock_a_df['date'])
    # 数据类型转换
    numeric_columns = ['open', 'close', 'high', 'low', 'volume']
    stock_a_df[numeric_columns] = stock_a_df[numeric_columns].apply(pd.to_numeric, errors='coerce')

    # 删除空值
    stock_a_df = stock_a_df.dropna()

    stock_a_df = stock_a_df.sort_values('date')

    # 计算移动平均线
    stock_a_df['MA5'] = stock_a_df['close'].rolling(window=5).mean()
    stock_a_df['MA10'] = stock_a_df['close'].rolling(window=10).mean()
    stock_a_df['MA20'] = stock_a_df['close'].rolling(window=20).mean()

    # 计算RSI指标
    delta = stock_a_df['close'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    stock_a_df['RSI'] = 100 - (100 / (1 + rs))
    # 计算MACD指标
    exp1 = stock_a_df['close'].ewm(span=12, adjust=False).mean()
    exp2 = stock_a_df['close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    stock_a_df['MACD'] = macd
    stock_a_df['Signal'] = signal
    stock_a_df['Histogram'] = macd - signal
    

    print(stock_a_df)

    # ak.stock_zh_a_hist()  历史数据
    # ak.stock_zh_a_spot_em()  # 实时数据
    # akshare.stock_bid_ask_em()
    # cache_manager = StockCache()
    # cache_manager.update_cache()
    # run_job(cache_manager)