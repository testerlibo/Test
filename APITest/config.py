# ===================== 你的真实测试服地址 =====================
BASE_URL = "http://192.168.0.250:8311"

# ===================== 所有接口统一管理 =====================
API = {
    # 登录
    "login": "/api/login/acc_login",
    # 你后续加接口 只在这里加！

    "bag": "/api/item/bag",
    "mail": "/api/mail/list",
    "use_item": "/api/item/use",
}

# ===================== 请求头（你抓包的真实头）=====================
HEADERS = {
    "User-Agent": "UnityPlayer/2021.3.10f1c2 (UnityWebRequest/1.0, libcurl/7.80.0-DEV)",
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Accept-Encoding": "deflate, gzip",
    "Connection": "Keep-Alive",
    "X-Unity-Version": "2021.3.10f1c2"
}

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