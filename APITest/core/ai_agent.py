import requests
from config import AI_CONFIG

class AITestAgent:
    def __init__(self):
        self.api_key = AI_CONFIG["api_key"]
        self.base_url = AI_CONFIG["base_url"]
        self.model = AI_CONFIG["model"]

    def chat(self, prompt):
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "你是专业游戏接口测试专家，回答精简、准确、不啰嗦。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": AI_CONFIG.get("temperature", 0.1)
            }

            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15
            )

            if resp.status_code != 200:
                return f"AI 服务异常 {resp.status_code}：{resp.text}"

            res_json = resp.json()

            if "choices" not in res_json or len(res_json["choices"]) == 0:
                return "AI 回复格式错误"

            return res_json["choices"][0]["message"]["content"]

        except Exception as e:
            return f"AI 调用失败：{str(e)}"

    def gen_test_cases(self, api_name, api_path, params):
        prompt = f"""
你是游戏接口测试专家。
接口：{api_name}
地址：{api_path}
入参：{params}

生成5条标准测试用例：
1.正常用例
2.参数缺失
3.参数非法
4.参数越界
5.重复请求

只输出用例条目，不要多余描述。
"""
        return self.chat(prompt)

    def assert_result(self, req, resp):
        prompt = f"""
分析游戏接口结果：
请求：{req}
响应：{resp}

判断：
1. 是否成功
2. code 是否正常
3. 是否存在BUG
4. 结论

输出精简。
"""
        return self.chat(prompt)

ai = AITestAgent()