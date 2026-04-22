# api地址
BASE_URL = "http://192.168.0.250:8311/api/"
# BASE_URL = "http://maoge-test-webserver.qikelizhi.com/api/"


# AI 大模型配置 deepseek
# AI_CONFIG = {
#     "api_key": "sk-fb7cbece201540d5aec83eaed5d41238",
#     "base_url": "https://api.deepseek.com",  # 可替换国内大模型地址
#     "model": "deepseek-chat",
#     "temperature": 0.3
# }
# AI 大模型配置 千问
AI_CONFIG = {
    "api_key": "sk-5907fdc40c1046f8bc3ce79015a65656",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "model": "qwen-turbo",  # 免费额度足够用
    "temperature": 0.1
}

# 数据库校验（可选）
DB_CONFIG = {}


CLIENT_META = {
    "clientVer": "0.8.1",
    "resVer": "4.3.23",
    "clientSys": 1,
    "packageName": "com.cikgames.cat.webgl",
    "userFromChannel": 2,
    "adId": ""
}

# 接口信息
API_INFO = {
    "client_res_ver": {
        "name": "资源版本号",
        "method": "GET",
        "url": "login/client_res_ver",
        "default": {
            "channelId": 1,
            "clientVer": "0.8.1",
            "clientSys": 1
        }
    },
    "acc_login": {
        "name": "账号登录",
        "method": "POST",
        "url": "login/acc_login",
        "default": {
            "channelLoginWay": 1,
            "channelId": 1,
            "channelAcc": "qz03311700",
            "credential": "123456",
            "clientMeta": CLIENT_META
        }
    },
    "default_choose_server": {
        "name": "获取默认服",
        "method": "POST",
        "url": "login/default_choose_server",
        "default": {
            "clientMeta": CLIENT_META
        }
    },
    "server_zone_list": {
        "name": "服务器大区列表",
        "method": "POST",
        "url": "login/server_zone_list",
        "default": {
            "clientMeta": CLIENT_META
        }
    },
    "server_list": {
        "name": "服务器列表",
        "method": "POST",
        "url": "login/server_list",
        "default": {
            "getListType": 1,
            "zoneId": 1,
            "clientMeta": CLIENT_META
        }
    },
    "player_login": {
        "name": "玩家登录",
        "method": "POST",
        "url": "login/player_login",
        "default": {
            "serverId": 1,
            "clientMeta": CLIENT_META
        }
    }
}

HEADERS = {
    "User-Agent": "UnityPlayer/2021.3.10f1c2",
    "Content-Type": "application/json",
}
