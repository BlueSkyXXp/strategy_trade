import logging
from datetime import datetime

import pandas as pd

# 配置日志
from app.core.log_config import setup_logger

logger = setup_logger(__name__)

# 导入 TradeService 类
from app.core.trade_service import TradeService
# 假设导入 StockService 类
from app.core.stock_service import StockService

# 全局变量用于内存缓存
class StockCache:
    # 类属性作为全局缓存
    YESTERDAY_LIMIT_UP_STOCKS = pd.DataFrame()  # 修改为 DataFrame 类型
    POSITION = []
    BALANCE = 0

    @classmethod
    def save_stocks_to_cache(cls, stocks, position=None, balance=None):
        """
        将股票列表、当前仓位和资金保存到内存缓存中
        """
        try:
            if isinstance(stocks, pd.DataFrame):
                cls.YESTERDAY_LIMIT_UP_STOCKS = stocks
            else:
                logger.warning("传入的昨日涨停数据不是 DataFrame 类型，无法保存")
            cls.POSITION = position if position is not None else []
            cls.BALANCE = balance if balance is not None else 0
            logger.info("成功保存股票信息到缓存")
        except Exception as e:
            logger.error(f"保存股票信息到缓存时出错: {e}")

    @classmethod
    def load_stocks_from_cache(cls):
        """
        从内存缓存中加载股票列表、当前仓位和资金
        """
        try:
            logger.info("成功从缓存加载股票信息")
            return cls.YESTERDAY_LIMIT_UP_STOCKS, cls.POSITION, cls.BALANCE
        except Exception as e:
            logger.error(f"从缓存加载股票信息时出错: {e}")
            return pd.DataFrame(), [], 0

    @classmethod
    def update_cache(cls):
        """
        更新内存缓存，重新从服务获取昨日涨停股票池、持仓、余额和交易日历信息
        """
        try:
            stock_service = StockService()
            trade_service = TradeService()

            # 从 stock 服务获取昨日涨停股票池
            limit_up_stocks_df = stock_service.get_stock_yesterday_zt_pool(date=datetime.now().strftime('%Y%m%d'))
            if isinstance(limit_up_stocks_df, pd.DataFrame) and not limit_up_stocks_df.empty:
                cls.YESTERDAY_LIMIT_UP_STOCKS = limit_up_stocks_df
                logger.info("成功更新昨日涨停股票池缓存")
                logger.info(limit_up_stocks_df)
            else:
                cls.YESTERDAY_LIMIT_UP_STOCKS = pd.DataFrame()
                logger.warning("未能成功获取昨日涨停股票池，已清空缓存或使用原有缓存")

            position_result = trade_service.get_position()
            if position_result and position_result.get('code') == 0:
                cls.POSITION = position_result.get('data', [])
                logger.info("成功更新持仓信息缓存")
                logger.info(position_result)
            else:
                logger.warning("未能成功获取持仓信息，使用原有缓存")

            balance_result = trade_service.get_balance()
            if balance_result and balance_result.get('code') == 0:
                data = balance_result.get('data', {})
                cls.BALANCE = float(data.get('可用金额', 0))
                logger.info("成功更新余额信息缓存")
                logger.info(data)
            else:
                logger.warning("未能成功获取余额信息，使用原有缓存")

            # 调用新的更新交易日历方法
            cls.update_trading_calendar()

        except Exception as e:
            logger.error(f"更新缓存时出错: {e}")

    @classmethod
    def update_trading_calendar(cls):
        """
        仅更新交易日历缓存
        """
        try:
            stock_service = StockService()
            # 从 stock 服务获取最新交易日历
            trading_calendar_df = stock_service.get_recent_trading_calendar()
            if isinstance(trading_calendar_df, pd.DataFrame) and not trading_calendar_df.empty:
                cls.TRADING_CALENDAR = trading_calendar_df
                logger.info("成功更新交易日历缓存")
                logger.info(trading_calendar_df)
            else:
                cls.TRADING_CALENDAR = pd.DataFrame()
                logger.warning("未能成功获取交易日历，已清空缓存或使用原有缓存")
        except Exception as e:
            logger.error(f"更新交易日历缓存时出错: {e}")

    @classmethod
    def get_trading_calendar(cls):
        """
        从缓存中获取交易日历
        """
        try:
            logger.info("成功从缓存获取交易日历")
            return cls.TRADING_CALENDAR
        except Exception as e:
            logger.error(f"从缓存获取交易日历时出错: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    try:
        # 测试更新缓存
        StockCache.update_cache()

        # 测试从缓存加载数据
        limit_up_stocks, position, balance = StockCache.load_stocks_from_cache()

        print("昨日涨停股票池:")
        print(limit_up_stocks)
        print("当前持仓:")
        print(position)
        print("当前余额:")
        print(balance)

        # 测试保存数据到缓存
        new_stocks = pd.DataFrame({'test': [1, 2, 3]})
        new_position = [{'stock': 'test_stock', 'amount': 100}]
        new_balance = 10000
        StockCache.save_stocks_to_cache(new_stocks, new_position, new_balance)

        # 再次测试从缓存加载数据
        limit_up_stocks, position, balance = StockCache.load_stocks_from_cache()

        print("\n更新后的昨日涨停股票池:")
        print(limit_up_stocks)
        print("更新后的当前持仓:")
        print(position)
        print("更新后的当前余额:")
        print(balance)

    except Exception as e:
        logger.error(f"测试 StockCache 时出错: {e}")