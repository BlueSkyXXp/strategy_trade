import requests

class TradeService:
    def __init__(self):
        self.base_url = 'http://10.37.81.24:5000'
        self.headers = {
            'Authorization': 'Bearer DSTdqw3Poq1mBzjY8OEUv6Zjl1JAHYoc'
        }
        self.data = {"action": "balance"}

    def _make_request(self, method, url, params=None, json=None):
        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                if method == 'get':
                    response = requests.get(url, headers=self.headers, params=params, json=json)
                # 可根据需要添加其他请求方法
                if response.status_code != 200:
                    print(f"请求失败，状态码: {response.status_code}，重试次数: {retries + 1}/{max_retries}")
                r = response.json()
                if r['code'] != 0:
                    print(f"请求失败，响应内容: {r}，重试次数: {retries + 1}/{max_retries}")
                return r
            except requests.RequestException as e:
                print(f"请求发生异常: {e}，重试次数: {retries + 1}/{max_retries}")
            retries += 1
        print("达到最大重试次数，请求失败")
        return None

    def get_balance(self):
        url = f"{self.base_url}/balance"
        return self._make_request('get', url, json=self.data)

    def get_position(self):
        url = f"{self.base_url}/position"
        return self._make_request('get', url)

    def buy_stock(self, stock_code, price, amount):
        url = f"{self.base_url}/buy"
        params = {
            "stock_no": stock_code,
            "price": price,
            "amount": amount
        }
        return self._make_request('get', url, params=params)

    def get_success_orders(self):
        url = f"{self.base_url}/success_orders"
        return self._make_request('get', url)

    def get_filled_orders(self):
        url = f"{self.base_url}/filled_orders"
        return self._make_request('get', url)

if __name__ == "__main__":
    trade_service = TradeService()
    balance = trade_service.get_balance()
    if balance:
        print(balance)
    position = trade_service.get_position()
    if position:
        print(position)
    success_orders = trade_service.get_success_orders()
    if success_orders:
        print(success_orders)
    filled_orders = trade_service.get_filled_orders()
    if filled_orders:
        print(filled_orders)
