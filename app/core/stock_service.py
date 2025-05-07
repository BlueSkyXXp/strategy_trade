import datetime

import pandas as pd
import requests
import akshare as ak

class StockService:
    # 替换为实际的 API 地址
    api_url = "https://push2.eastmoney.com/api/qt/clist/get"
    market_movement_url = "https://push2ex.eastmoney.com/getAllStockChanges"
    yesterday_zt_pool_url = "https://push2ex.eastmoney.com/getYesterdayZTPool"

    OPEN_TIME = (
        (datetime.time(9, 15, 0), datetime.time(11, 30, 0)),
        (datetime.time(13, 0, 0), datetime.time(15, 0, 0)),
    )

    def __init__(self):
        """
        初始化 StockService 类
        """
        pass

    def is_trade_date(self, date=None):
        url = "https://www.szse.cn/api/report/exchange/onepersistenthour/monthList"
        r = requests.get(url)
        resp_json = r.json()
        if resp_json is None or resp_json['data'] is None:
            return False
        df = pd.DataFrame(resp_json['data'])
        result = df[(df['jyrq'] == date) & (df['jybz'] == '1')]
        return not result.empty

    def get_recent_trading_calendar(self):
        """
        发送请求获取最近的交易日历
        :return: 包含最近交易日历的 DataFrame，如果请求失败则返回 None
        """
        url = "https://www.szse.cn/api/report/exchange/onepersistenthour/monthList"
        try:
            r = requests.get(url)
            resp_json = r.json()
            if resp_json is None or resp_json['data'] is None:
                return None
            df = pd.DataFrame(resp_json['data'])
            # 筛选出交易标识为 '1' 的记录，即交易日
            trading_days = df[df['jybz'] == '1']
            # 删除两列 zrxh jybz
            trading_days = trading_days.drop(columns=['zrxh', 'jybz'])
            return trading_days
        except requests.RequestException as e:
            print(f"请求最近交易日历时发生异常: {e}")
            return None

    def is_trade_time(self, now_time):
        """
        判断是否是交易时间
        :return:
        """
        for start, end in self.OPEN_TIME:
            if start <= now_time <= end:
                return True
        return False

    def get_stock_data(self):
        """
        发送请求获取股票数据
        :return: 包含股票数据的响应内容，如果请求失败则返回 None
        """
        try:
            response = requests.get(self.api_url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"请求失败，状态码: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"请求发生异常: {e}")
            return None

    def get_market_movement_data(self):
        """
        发送请求获取盘口异动数据
        :return: 包含盘口异动数据的响应内容，如果请求失败则返回 None
        """

        # curl --location 'https://push2ex.eastmoney.com/getAllStockChanges?ut=7eea3edcaed734bea9cbfc24409ed989&type=8293%2C64&pageindex=0&pagesize=64&dpt=wzchanges'
        params={
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "type": "8193",
            "pageindex": "0",
            "pagesize": "64",
            "dpt": "wzchanges"
        }
        try:
            response = requests.get(url=self.market_movement_url, params=params, timeout=15)
            resp_json = response.json()
            if resp_json is None:
                return None
            if resp_json['data'] is None:
                return None
            return resp_json['data']['allstock']
            
        except requests.RequestException as e:
            print(f"请求盘口异动数据时发生异常: {e}")
            return None

    def get_board_concept_stock_top_ten(self):
        """
        发送请求获取板块概念股票数据
        :return: 包含板块概念股票数据的响应内容，如果请求失败则返回 None
        """
        # curl --location 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&ut=fa5fd1943c7b386f172d6893dbfba10b&fltt=1&invt=2&fid=f3&fs=m%3A90+t%3A3+f%3A!50&fields=f12%2Cf13%2Cf14%2Cf1%2Cf2%2Cf4%2Cf3%2Cf152%2Cf20%2Cf8%2Cf104%2Cf105%2Cf128%2Cf140%2Cf141%2Cf207%2Cf208%2Cf209%2Cf136%2Cf222'
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params={
            "pn": "1",
            "pz": "10",
            "po": "1",
            "np": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fltt": "1",
            "invt": "2",
            "fid": "f3",
            "fs": "m:90+t:3+f:!50",
            "fields": "f12,f13,f14,f1,f2,f4,f3,f152,f20,f8,f104,f105,f128,f140,f141,f207,f208,f209,f136,f222"
        }
        try:
            response = requests.get(url=url, params=params, timeout=15)
            resp_json = response.json()
            if resp_json is None:
                return None
            if resp_json['data'] is None:
                return None
            return pd.DataFrame(resp_json['data']['diff'])

        except requests.RequestException as e:
            print(f"请求板块概念股票数据时发生异常: {e}")
            return None

    def get_board_concept_stock_cons_top_twenty(self, board_concept_code):
        """
        发送请求获取板块概念股票数据
        :return: 包含板块概念股票数据的响应内容，如果请求失败则返回 None
        """
        # curl--location'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&ut=fa5fd1943c7b386f172d6893dbfba10b&fltt=1&invt=2&fid=f62&fs=b:BK1098&fields=f14,f12,f13,f1,f2,f4,f3,f152,f128,f140,f141,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f109,f160,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183'
        param = {
            "pn": "1",
            "pz": "20",
            "po": "1",
            "np": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fltt": "1",
            "invt": "2",
            "fid": "f3",
            "fs": f"b:{board_concept_code}",
            "fields": "f14,f12,f13,f1,f2,f4,f3,f21,f152,f128,f140,f141,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f109,f160,f164,f165,f166,f167,f168,f169,f170,f171,f172,f173,f174,f175,f176,f177,f178,f179,f180,f181,f182,f183"
        }
        try:
            response = requests.get(url=self.api_url, params=param, timeout=15)
            resp_json = response.json()
            if resp_json is None:
                return None
            if resp_json['data'] is None:
                return None
            return pd.DataFrame(resp_json['data']['diff'])
        except requests.RequestException as e:
            print(f"请求板块概念股票数据时发生异常: {e}")
            return None
    
    def get_stock_yesterday_zt_pool(self, date=None):
        """
        发送请求获取昨日涨停股票数据
        :return: 包含昨日涨停股票数据的响应内容，如果请求失败则返回 None
        """
        # curl --location 'https://push2ex.eastmoney.com/getYesterdayZTPool?ut=7eea3edcaed734bea9cbfc24409ed989&dpt=wz.ztzt&Pageindex=0&pagesize=6&sort=zs%3Adesc&date=20250428'
        param = {
            "ut": "7eea3edcaed734bea9cbfc24409ed989",
            "dpt": "wz.ztzt",
            "Pageindex": "0",
            "pagesize": "50",
            "sort": "zs:desc",
            "date": date
        }
        try:
            response = requests.get(url=self.yesterday_zt_pool_url, params=param, timeout=15)
            resp_json = response.json()
            if resp_json is None:
                return None
            if resp_json['data'] is None:
                return None
            return pd.DataFrame(resp_json['data']['pool'])
        except requests.RequestException as e:
            print(f"请求昨日涨停股票数据时发生异常: {e}")
            return None

    #  上证股票涨幅榜
    def get_stock_sh_zs_rank(self, date=None):
        """
        发送请求获取上证股票涨幅榜数据
        :return: 包含上证股票涨幅榜数据的响应内容，如果请求失败则返回 None
        """
        # curl --location 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&ut=fa5fd1943c7b386f172d6893dbfba10b&fltt=1&invt=2&fid=f3&fs=m%3A1+t%3A2%2Cm%3A1+t%3A23&fields=f12%2Cf13%2Cf14%2Cf1%2Cf2%2Cf4%2Cf3%2Cf152%2Cf5%2Cf6%2Cf7%2Cf15%2Cf18%2Cf16%2Cf17%2Cf10%2Cf8%2Cf9%2Cf21%2Cf22%2Cf23%2Cf24%2Cf62%2Cf72'
        param = {
            "pn": "1",
            "pz": "50",
            "po": "1",
            "np": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fltt": "1",
            "invt": "2",
            "fid": "f3",
            "fs": "m:1+t:2,m:1+t:23",
            "fields": "f12,f13,f14,f1,f2,f4,f3,f152,f5,f6,f7,f15,f18,f16,f17,f10,f8,f9,f21,f22,f23,f24,f62,f72"
        }
        try:
            response = requests.get(url=self.api_url, params=param, timeout=15)
            resp_json = response.json()
            if resp_json is None:
                return None
            if resp_json['data'] is None:
                return None
            return resp_json['data']['diff']
        except requests.RequestException as e:
            print(f"请求上证股票涨幅榜数据时发生异常: {e}")
            return None
    #  深证股票涨幅榜
    def get_stock_sz_zs_rank(self, date=None):
        """
        发送请求获取深证股票涨幅榜数据
        :return: 包含深证股票涨幅榜数据的响应内容，如果请求失败则返回 None
        """
        # curl --location 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=20&po=1&np=1&ut=fa5fd1943c7b386f172d6893dbfba10b&fltt=1&invt=2&fid=f3&fs=m%3A0+t%3A6%2Cm%3A0+t%3A80&fields=f12%2Cf13%2Cf14%2Cf1%2Cf2%2Cf4%2Cf3%2Cf152%2Cf5%2Cf6%2Cf7%2Cf15%2Cf18%2Cf16%2Cf17%2Cf10%2Cf8%2Cf9%2Cf21%2Cf22%2Cf23%2Cf24%2Cf62%2Cf72'
        param = {
            "pn": "1",
            "pz": "50",
            "po": "1",
            "np": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fltt": "1",
            "invt": "2",
            "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80",
            "fields": "f12,f13,f14,f1,f2,f4,f3,f152,f5,f6,f7,f15,f18,f16,f17,f10,f8,f9,f21,f22,f23,f24,f62,f72"
        }
        try:
            response = requests.get(url=self.api_url, params=param, timeout=15)
            resp_json = response.json()
            if resp_json is None:
                return None
            if resp_json['data'] is None:
                return None
            return resp_json['data']['diff']
        except requests.RequestException as e:
            print(f"请求深证股票涨幅榜数据时发生异常: {e}")
            return None

    # 上证股票涨速榜
    def get_stock_sh_zs_speed_rank(self, date=None):
        """
        发送请求获取上证股票涨速榜数据
        :return: 包含上证股票涨速榜数据的响应内容，如果请求失败则返回 None
        """
        param = {
            "pn": "1",
            "pz": "10",
            "po": "1",
            "np": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fltt": "1",
            "invt": "2",
            "fid": "f22",
            "fs": "m:1+t:2,m:1+t:23",
            "fields": "f12,f13,f14,f1,f2,f4,f3,f152,f5,f6,f7,f15,f18,f16,f17,f10,f8,f9,f21,f22,f23,f24,f62,f72"
        }
        try:
            response = requests.get(url=self.api_url, params=param, timeout=15)
            resp_json = response.json()
            if resp_json is None:
                return None
            if resp_json['data'] is None:
                return None
            return resp_json['data']['diff']
        except requests.RequestException as e:
            print(f"请求上证股票涨幅榜数据时发生异常: {e}")
            return None

    # 深证股票涨速榜
    def get_stock_sz_zs_speed_rank(self, date=None):
        """
        发送请求获取深证股票涨速榜数据
        :return: 包含深证股票涨速榜数据的响应内容，如果请求失败则返回 None
        """
        param = {
            "pn": "1",
            "pz": "10",
            "po": "1",
            "np": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "fltt": "1",
            "invt": "2",
            "fid": "f22",
            "fs": "m:0+t:6,m:0+t:80",
            "fields": "f12,f13,f14,f1,f2,f4,f3,f152,f5,f6,f7,f15,f18,f16,f17,f10,f8,f9,f21,f22,f23,f24,f62,f72"
        }
        try:
            response = requests.get(url=self.api_url, params=param, timeout=15)
            resp_json = response.json()
            if resp_json is None:
                return None
            if resp_json['data'] is None:
                return None
            return resp_json['data']['diff']
        except requests.RequestException as e:
            print(f"请求深证股票涨幅榜数据时发生异常: {e}")
            return None

    # 行情报价
    def stock_bid_ask_em(self, symbol: str = "000001") -> pd.DataFrame:
        """
        东方财富-行情报价
        https://quote.eastmoney.com/sz000001.html
        :param symbol: 股票代码
        :type symbol: str
        :return: 行情报价
        :rtype: pandas.DataFrame
        """
        url = "https://push2.eastmoney.com/api/qt/stock/get"
        market_code = 1 if symbol.startswith("6") else 0
        params = {
            "fltt": "2",
            "invt": "2",
            "fields": "f120,f121,f122,f174,f175,f59,f163,f43,f57,f58,f169,f170,f46,f44,f51,"
            "f168,f47,f164,f116,f60,f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,"
            "f135,f136,f137,f138,f139,f141,f142,f144,f145,f147,f148,f140,f143,f146,"
            "f149,f55,f62,f162,f92,f173,f104,f105,f84,f85,f183,f184,f185,f186,f187,"
            "f188,f189,f190,f191,f192,f107,f111,f86,f177,f78,f110,f262,f263,f264,f267,"
            "f268,f255,f256,f257,f258,f127,f199,f128,f198,f259,f260,f261,f171,f277,f278,"
            "f279,f288,f152,f250,f251,f252,f253,f254,f269,f270,f271,f272,f273,f274,f275,"
            "f276,f265,f266,f289,f290,f286,f285,f292,f293,f294,f295",
            "secid": f"{market_code}.{symbol}",
        }
        r = requests.get(url, params=params)
        data_json = r.json()
        # f51 是涨停价 f52 是跌停价
        # f31-f40 依次卖一到卖五的价格和委托量
        # f41-f50 依次买一到买五的价格和委托量

        data_dict = data_json["data"]
        data_df = pd.DataFrame([data_dict])
        return data_df

        
if __name__ == "__main__":
    stock_service = StockService()
    trade_candle = stock_service.get_recent_trading_calendar()
    print(trade_candle)
    # 格式得是20250429 str 今天的时间
    # date = datetime.datetime.now().strftime("%Y%m%d")
    # stock_data = stock_service.get_stock_yesterday_zt_pool(date=date)
    # print(stock_data)

    bid_df = stock_service.stock_bid_ask_em(symbol="300255")


    # 确保 zt_price 是一个有效的数值
    if 'f51' in bid_df.columns:
        zt_price = bid_df['f51'].values[0] if len(bid_df['f51'].values) > 0 else 0

    # 1万元，以涨停价买入，买入数量为100及其整数倍
    if zt_price > 0:
        # 修改此处，确保 buy_num 是 100 的整数倍
        buy_num = (int(10000 / zt_price) // 100) * 100
        print(buy_num)

    print(zt_price)

    # buy_resp = trade_api.buy_stock(stock_code=stock_code, price=zt_price / 100.0, amount=buy_num)
    # if buy_resp and buy_resp.get('code') == 0:
    #     logger.info("买入成功，股票代码：%s,买入数量：%s,买入价格:%s", stock_code, buy_num, zt_price / 100.0)
    #     cache_manager.BALANCE = cache_manager.BALANCE - buy_num * zt_price / 100.0
    # else:
    #     logger.error("买入失败，股票代码：%s,买入数量：%s,买入价格:%s", stock_code, buy_num, zt_price / 100.0)
    print(bid_df)
    print(buy_num)