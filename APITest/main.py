from core.api_client import api
from core.ai_agent import ai
from core.case_parser import parse_cases_from_ai
from core.case_bundle import ensure_one_normal_four_negative
from core.report import report
from config import API_INFO

def run_test():
    print("=" * 70)
    print("🤖 AI 动态用例自动化测试")
    print("=" * 70)

    # 登录
    print("\n🔐 登录中...")
    login_resp = api.req("acc_login", API_INFO["acc_login"]["default"])
    print("登录结果:", login_resp)

    if login_resp.get("code") != 0:
        print("❌ 登录失败")
        return

    token = login_resp["data"]["token"]
    api.set_token(token)
    print("✅ Token 已设置")

    report_list = []

    # 遍历接口
    for api_key, info in API_INFO.items():
        if api_key == "acc_login":
            continue

        api_name = info["name"]
        default_params = info["default"]

        print("\n" + "="*60)
        print(f"🎯 接口：{api_name}")
        print("="*60)

        # AI 生成用例
        case_text = ai.gen_test_cases_with_params(api_name, default_params)
        print(f"\n📋 AI 用例：\n{case_text}")

        cases, parse_warnings = parse_cases_from_ai(case_text)
        cases, bundle_warnings = ensure_one_normal_four_negative(cases, default_params)
        for w in parse_warnings + bundle_warnings:
            print(f"⚠️ 解析/归一化：{w}")
        print(f"📌 本接口执行用例数：{len(cases)}（1 条 normal + 4 条 negative）")

        # 执行
        for row in cases:
            case_name = row["case"]
            kind = row["kind"]
            param = row["params"]

            api.set_token(token)
            print(f"\n▶ 执行：{case_name}（kind={kind}）")
            print(f"🔎 请求：{param}")

            resp = api.req(api_key, param)
            print(f"📦 返回：{resp}")

            ai_result = ai.analyze(resp, kind)
            print(f'📊结论是:\n{ai_result}')

            report_list.append({
                "api": api_name,
                "case": case_name,
                "kind": kind,
                "req": param,
                "resp": resp,
                "ai": ai_result
            })

    # ======================
    # 统一输出报告
    # ======================
    report.generate(report_list)   # 控制台
    report.save_txt(report_list)    # txt报告
    report.save_json(report_list)   # json报告
    report.save_html(report_list)

if __name__ == "__main__":
    run_test()