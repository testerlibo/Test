from core.api_client import api
from core.ai_agent import ai

def test_game_with_ai():
    print("=" * 50)
    print("🤖 AI 自动生成登录接口测试用例")
    cases = ai.gen_test_cases(
        "登录接口",
        "/api/login/acc_login",
        {"channelAcc": "str", "credential": "str", "clientMeta": "dict"}
    )
    print(cases)
    print("=" * 50)

    # 登录
    resp = api.login()
    print("登录返回：", resp)

    # AI 自动分析结果
    print("\n🔍 AI 自动分析：")
    print(ai.assert_result({"action": "login"}, resp))


    print("\n🎉 AI 自动化测试完成！")

if __name__ == "__main__":
    test_game_with_ai()