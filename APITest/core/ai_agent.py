import requests
import json
from config import AI_CONFIG
from core.result_judge import expectation_met

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
        body_json = json.dumps(default_body, ensure_ascii=False)
        prompt = f"""接口：{api_name}
正确参数示例：{body_json}

【硬性要求】只输出一个 JSON 数组，且数组长度必须恰好为 5。
其中恰好 1 条 kind 为 normal，恰好 4 条 kind 为 negative。建议顺序：第 1 条 normal，第 2～5 条 negative。
不要输出数组以外的任何字符（不要 Markdown 围栏、不要解释、不要前后缀文字）。

覆盖建议：1 次正常请求；4 次异常/边界（如空参、缺字段、类型或取值非法、无意义额外字段等）。

每个元素对象字段：
- kind：只能是 normal 或 negative（normal=期望 code=0 成功；negative=期望 code≠0）
- name：用例简称
- params：请求体（JSON 对象）

示例（结构示意，请把 params 换成本接口真实字段）：
[
  {{"kind":"normal","name":"正常","params":{body_json}}},
  {{"kind":"negative","name":"空参","params":{{}}}},
  {{"kind":"negative","name":"缺参","params":{{}}}},
  {{"kind":"negative","name":"非法","params":{{}}}},
  {{"kind":"negative","name":"异常","params":{{}}}}
]
"""
        return self.chat(prompt)

    @staticmethod
    def analyze(resp, kind: str):
        code = resp.get("code")
        met = expectation_met(resp, kind)
        label = "正向(期望成功)" if kind == "normal" else "异常/边界(期望失败码)"

        has_code = code is not None
        code_desc = "code 存在" if has_code else "code 缺失或格式异常"

        return (
            f"用例类型（kind={kind}）：{label}\n"
            f"{code_desc}：code={code}\n"
            f"是否符合预期：{'是' if met else '否'}\n"
            f"结论：{'接口行为符合预期' if met else '接口返回与预期不符'}"
        )


ai = AITestAgent()