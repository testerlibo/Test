from core.api_client import api
from core.ai_agent import ai
from config import API_INFO
import json

def run_ai_dynamic_test():
    # 登录获取Token
    print("\n🔐 登录获取Token...")
    login_api = API_INFO["acc_login"]
    login_resp = api.req("acc_login", login_api["default"])
    print("登录结果:", login_resp)
    if login_resp.get("code") != 0:
        print("❌ 登录失败")
        return
    token = login_resp["data"]["token"]
    api.set_token(token)
    print("✅ Token 已生效： ", token)

    report = [] #保存结果
    # 遍历接口
    for api_key, info in API_INFO.items():
        api_name = info["name"]
        default_params = info["default"]
        print(f"🎯 接口：{api_name}")
        #生成用例
        case_text = ai.gen_test_cases_with_params(api_name, default_params)
        print(f"\n📋 AI 生成用例：\n{case_text}")

        lines = []
        for line in case_text.splitlines():
            line = line.strip()
            if line and "|" in line:
                lines.append(line)
        for line in lines:
            try:
                case_name, param_str = line.split("|", 1)
                param = json.loads(param_str)
            except:
                print(f"⚠️ 跳过：{line}")
                continue
            # 执行用例
            api.set_token(token)
            print(f"\n▶ 执行：{case_name}")
            print(f"🔎 请求：{param}")
            resp = api.req(api_key, param)
            print(f"📦 返回：{resp}")
            # 执行结果
            ai_result = ai.analyze(resp, case_name)
            print(f"✅ AI分析：{ai_result}")
            report.append({
                "api": api_name,
                "case": case_name,
                "req": param,
                "resp": resp,
                "ai": ai_result
            })
    print("📊 AI 动态执行报告")
    for item in report:
        code = item["resp"].get("code")
        status = "✅ 正常" if code == 0 else "⚠️ 预期异常"
        print(f"[{item['api']}] {item['case']} | {status}")
        print(f"   请求：{item['req']}")
        print(f"   AI：{item['ai']}")
        print("-"*60)

    print("\n🎉 AI 全动态自动化测试完成！")

if __name__ == "__main__":
    run_ai_dynamic_test()