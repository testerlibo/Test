import requests
import json
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
                    {"role": "system", "content": "你是专业接口测试专家，严格按规则判断"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }
            resp = requests.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=10)
            if resp.status_code != 200:
                return "AI服务异常"
            return resp.json()["choices"][0]["message"]["content"].strip()
        except:
            return "AI调用失败"

    def gen_test_cases_with_params(self, api_name, default_body):
        prompt = f"""
接口：{api_name}
正确参数：{default_body}

生成5条可执行测试用例，严格按格式返回，不要多余内容
每行格式：
用例名称|参数字典

1 正常用例|{json.dumps(default_body, ensure_ascii=False)}
2 空参|{{}}
3 缺少必选参数|{{}}
4 非法参数|{{}}
5 异常场景|{{}}
"""
        return self.chat(prompt)
    def analyze(self, resp, case_name=""):
        prompt = f"""
接口返回：{resp}
用例名称：{case_name}

请严格按照以下规则判断，精简输出4行：
1. 是否成功
2. code是否正常
3. 是否符合预期
4. 结论

规则：
1. 正常用例 → code=0 = 成功 = 符合预期
2. 异常用例（空参、缺参、非法、异常）→ code≠0 = 异常 = 符合预期
"""
        return self.chat(prompt)

ai = AITestAgent()