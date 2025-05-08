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
    # 昨日跌停股票池
    YESTERDAY_LIMIT_DOWN_STOCKS = pd.DataFrame()

    POSITION = []
    BALANCE = 0
    # 新增交易日历缓存变量
    TRADING_CALENDAR = pd.DataFrame()

    # 今日买成功的股票池
    TODAY_BUY_STOCKS = []

    # 今日买入板块id和数量，是个map
    TODAY_BUY_BOARD_IDS = {}

    @classmethod
    def get_yesterday_limit_down_stocks(cls):
        """
        从缓存中获取昨日跌停股票池
        :return: 昨日跌停股票池的 DataFrame
        """
        try:
            logger.info("成功从缓存获取昨日跌停股票池")
            return cls.YESTERDAY_LIMIT_DOWN_STOCKS
        except Exception as e:
            logger.error(f"从缓存获取昨日跌停股票池时出错: {e}")
            return pd.DataFrame()

    @classmethod
    def set_today_buy_board_id(cls, board_id, num):
        """
        设置今日买入板块中指定板块id的股票数量
        :param board_id: 板块id
        :param num: 该板块中股票的数量
        """
        try:
            if isinstance(board_id, (str, int)) and isinstance(num, (int, float)):
                cls.TODAY_BUY_BOARD_IDS[board_id] = num
                logger.info(f"成功设置板块 {board_id} 的今日买入股票数量为 {num}")
            else:
                logger.warning("传入的板块id或股票数量类型不正确，无法设置")
        except Exception as e:
            logger.error(f"设置板块 {board_id} 的今日买入股票数量时出错: {e}")

    @classmethod
    def append_today_buy_board_id(cls, board_id):
        """
        若今日买入板块id映射中不存在指定的board_id，则将其值设为1；若存在，则将其值加1
        :param board_id: 板块id
        """
        try:
            if isinstance(board_id, (str, int)):
                cls.TODAY_BUY_BOARD_IDS[board_id] = cls.TODAY_BUY_BOARD_IDS.get(board_id, 0) + 1
                logger.info(f"成功更新板块 {board_id} 的今日买入股票数量为 {cls.TODAY_BUY_BOARD_IDS[board_id]}")
            else:
                logger.warning("传入的板块id类型不正确，无法更新")
        except Exception as e:
            logger.error(f"更新板块 {board_id} 的今日买入股票数量时出错: {e}")

    @classmethod
    def get_today_buy_board_id(cls, board_id):
        """
        获取今日买入板块中指定板块id的股票数量
        :param board_id: 板块id
        :return: 该板块中股票的数量，如果不存在则返回0
        """
        try:
            result = cls.TODAY_BUY_BOARD_IDS.get(board_id, 0)
            if result == 0:
                logger.info(f"板块 {board_id} 今日买入股票数量不存在，返回默认值 0")
            else:
                logger.info(f"成功从缓存获取板块 {board_id} 的今日买入股票数量为 {result}")
            return result
        except Exception as e:
            logger.error(f"从缓存获取板块 {board_id} 的今日买入股票数量时出错: {e}")
            return 0

    @classmethod
    def append_today_buy_stock(cls, stock):
        """
        向今日买成功的股票池中添加单个股票
        :param stock: 要添加的股票
        """
        try:
            cls.TODAY_BUY_STOCKS.append(stock)
            logger.info(f"成功添加股票 {stock} 到今日买成功的股票池")
        except Exception as e:
            logger.error(f"向今日买成功的股票池添加股票 {stock} 时出错: {e}")

    @classmethod
    def remove_today_buy_stock(cls, stock):
        """
        从今日买成功的股票池中移除单个股票
        :param stock: 要移除的股票
        """
        try:
            if stock in cls.TODAY_BUY_STOCKS:
                cls.TODAY_BUY_STOCKS.remove(stock)
                logger.info(f"成功从今日买成功的股票池移除股票 {stock}")
            else:
                logger.warning(f"今日买成功的股票池中不存在股票 {stock}，无法移除")
        except Exception as e:
            logger.error(f"从今日买成功的股票池移除股票 {stock} 时出错: {e}")

    @classmethod
    def set_today_buy_stocks(cls, stocks):
        """
        设置今日买到的股票池
        :param stocks: 今日买到的股票列表
        """
        try:
            if isinstance(stocks, list):
                cls.TODAY_BUY_STOCKS = stocks
                logger.info("成功设置今日买到的股票池")
            else:
                logger.warning("传入的今日买到的股票数据不是列表类型，无法设置")
        except Exception as e:
            logger.error(f"设置今日买到的股票池时出错: {e}")

    @classmethod
    def get_today_buy_stocks(cls):
        """
        获取今日买到的股票池
        :return: 今日买到的股票列表
        """
        try:
            logger.info("成功从缓存获取今日买到的股票池")
            return cls.TODAY_BUY_STOCKS
        except Exception as e:
            logger.error(f"从缓存获取今日买到的股票池时出错: {e}")
            return []

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

            # 从 stock 服务获取昨日跌停股票池
            limit_down_stocks_df = stock_service.get_stock_dt_pool(date=datetime.now().strftime('%Y%m%d'))
            if isinstance(limit_down_stocks_df, pd.DataFrame) and not limit_down_stocks_df.empty:
                cls.YESTERDAY_LIMIT_DOWN_STOCKS = limit_down_stocks_df
                logger.info("成功更新昨日跌停股票池缓存")
                logger.info(limit_down_stocks_df)
            else:
                cls.YESTERDAY_LIMIT_DOWN_STOCKS = pd.DataFrame()
                logger.warning("未能成功获取昨日跌停股票池，已清空缓存或使用原有缓存")

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

            # 清理今日买成功的股票池
            cls.TODAY_BUY_STOCKS = []

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

    @classmethod
    def set_balance(cls, balance):
        """
        设置当前余额
        :param balance: 新的余额值
        """
        try:
            if isinstance(balance, (int, float)):
                cls.BALANCE = balance
                logger.info("成功设置当前余额")
            else:
                logger.warning("传入的余额数据不是数字类型，无法设置")
        except Exception as e:
            logger.error(f"设置当前余额时出错: {e}")

    @classmethod
    def get_balance(cls):
        """
        获取当前余额
        :return: 当前余额值
        """
        try:
            logger.info("成功从缓存获取当前余额")
            return cls.BALANCE
        except Exception as e:
            logger.error(f"从缓存获取当前余额时出错: {e}")
            return 0

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