import requests
from config import BASE_URL, API_INFO, HEADERS

class GameApiClient:
    def __init__(self):
        self.headers = HEADERS.copy()
        self.token = None

    def set_token(self, token):
        self.token = token

    def req(self, api_key, params=None):
        if params is None:
            params = {}

        api = API_INFO[api_key]
        url = BASE_URL + api["url"]
        method = api["method"].upper()

        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        try:
            if method == "POST":
                r = requests.post(url, json=params, headers=self.headers)
            elif method == "GET":
                r = requests.get(url, params=params, headers=self.headers)
            else:
                return {"code": -1, "msg": "不支持的请求方式"}

            if r.status_code == 401:
                return {"code": 401, "msg": "未授权，请登录"}
            return r.json()

        except Exception as e:
            return {"code": -99, "msg": str(e)}

api = GameApiClient()