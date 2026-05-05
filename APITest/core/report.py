# core/report.py
import json
from datetime import datetime

from core.result_judge import expectation_met_for_item

class TestReport:
    def __init__(self):
        self.start_time = datetime.now()

    def generate(self, report_list):
        """控制台简洁报告"""
        print("\n" + "="*70)
        print("📊 AI 接口自动化测试报告")
        print("="*70)
        print(f"开始时间：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总用例数：{len(report_list)}")
        print("-"*70)

        for item in report_list:
            api = item["api"]
            case = item["case"]
            code = item["resp"].get("code")
            ok = expectation_met_for_item(item)
            status = "✅ 符合预期" if ok else "❌ 不符合预期"
            print(f"【{api}】{case} | {status} code={code}")

        print("\n🎉 测试完成！")

    def save_txt(self, report_list, path="report.txt"):
        """文本报告"""
        with open(path, "w", encoding="utf-8") as f:
            f.write("=== 接口测试报告 ===\n")
            f.write(f"时间：{self.start_time}\n")
            f.write(f"总用例数：{len(report_list)}\n\n")
            for item in report_list:
                f.write(f"接口：{item['api']}\n")
                f.write(f"用例：{item['case']}\n")
                f.write(f"请求：{json.dumps(item['req'], ensure_ascii=False, indent=2)}\n")
                f.write(f"返回：{json.dumps(item['resp'], ensure_ascii=False, indent=2)}\n")
                f.write(f"AI分析：{item['ai']}\n")
                f.write("-" * 60 + "\n")

    def save_json(self, report_list, path="report.json"):
        """JSON报告"""
        out = {
            "start_time": str(self.start_time),
            "total": len(report_list),
            "cases": report_list
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)

    def save_html(self, report_list, path="report.html"):
        """HTML 精美网页报告"""
        total = len(report_list)
        met_cnt = sum(1 for it in report_list if expectation_met_for_item(it))
        unmet_cnt = total - met_cnt

        html = f'''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>接口测试报告</title>
<style>
body {{ font-family: Microsoft YaHei, sans-serif; margin: 20px; background: #f5f5f5; }}
.container {{ max-width: 1200px; margin: auto; background: white; padding: 24px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.header {{ text-align: center; margin-bottom: 20px; }}
.stats {{ display: flex; gap: 20px; justify-content: center; margin: 20px 0; }}
.stat {{ padding: 14px 24px; border-radius: 8px; color: white; font-weight: bold; }}
.total {{ background: #409eff; }}
.pass {{ background: #67c23a; }}
.fail {{ background: #f56c6c; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
th {{ background: #f9f9f9; }}
.pass-tag {{ color: #67c23a; font-weight: bold; }}
.fail-tag {{ color: #f56c6c; font-weight: bold; }}
.detail {{ margin-top: 8px; padding: 10px; background: #fafafa; border-radius: 4px; font-size: 13px; line-height: 1.6; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h2>AI 接口自动化测试报告</h2>
    <p>生成时间：{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
  </div>

  <div class="stats">
    <div class="stat total">总用例：{total}</div>
    <div class="stat pass">符合预期：{met_cnt}</div>
    <div class="stat fail">不符合预期：{unmet_cnt}</div>
  </div>

  <table>
  <tr><th>接口</th><th>用例</th><th>状态</th><th>Code</th><th>AI分析</th></tr>
        '''

        for item in report_list:
            api = item["api"]
            case = item["case"]
            resp = item["resp"]
            code = resp.get("code")
            ai = item["ai"].replace("\n", "<br>")

            req_json = json.dumps(item["req"], ensure_ascii=False, indent=2)
            resp_json = json.dumps(resp, ensure_ascii=False, indent=2)

            if expectation_met_for_item(item):
                tag = '<span class="pass-tag">✅ 符合预期</span>'
            else:
                tag = '<span class="fail-tag">❌ 不符合预期</span>'

            html += f'''
<tr>
  <td>{api}</td>
  <td>{case}</td>
  <td>{tag}</td>
  <td>{code}</td>
  <td>
    {ai}
    <div class="detail">
      <strong>请求：</strong><pre>{req_json}</pre>
      <strong>返回：</strong><pre>{resp_json}</pre>
    </div>
  </td>
</tr>
            '''

        html += '''
  </table>
</div>
</body>
</html>
        '''

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

report = TestReport()