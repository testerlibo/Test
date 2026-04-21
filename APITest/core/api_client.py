import requests
from config import BASE_URL, API, HEADERS

class GameApiClient:
    def __init__(self):
        self.headers = HEADERS.copy()
        self.token = None

    def login(self):
        """登录：自动获取token"""
        url = BASE_URL + API["login"]
        data = {
            "channelLoginWay": 1,
            "channelId": 1,
            "channelAcc": "qz03311700",
            "credential": "123456",
            "clientMeta": {
                "clientVer": "0.8.1",
                "resVer": "4.3.23",
                "clientSys": 1,
                "packageName": "com.cikgames.cat.webgl",
                "userFromChannel": 2,
                "adId": ""
            }
        }
        resp = requests.post(url, json=data, headers=self.headers).json()

        if resp.get("code") == 0:
            self.token = resp["data"]["token"]
            print("✅ 登录成功，token已自动设置")
        return resp

    def send(self, api_name, body=None):
        """
        统一发送请求
        :param api_name: API 里的key，如 login / role_list
        :param body: 接口参数
        """
        if body is None:
            body = {}

        # 自动拼接完整URL
        url = BASE_URL + API[api_name]

        # 自动带token
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        return requests.post(url, json=body, headers=self.headers).json()

# 全局单例
api = GameApiClient()