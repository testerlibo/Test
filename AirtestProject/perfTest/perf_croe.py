# -*- coding: utf-8 -*-
from datetime import datetime
import time
import threading
import os
import json


class PerformanceMonitor:
    def __init__(self, package_name, device_serial):
        self.package_name = package_name
        self.device_serial = device_serial
        self.is_running = False
        self.data_records = []
        self.monitor_thread = None

        # 固定：不需要参与统计、不需要画图表的字段（只做日志记录）
        self.exclude_stat_fields = ["timestamp", "record_time"]

    def start_monitoring(self, interval=1.0):
        """启动后台监控线程"""
        self.is_running = True
        self.data_records = []
        self.monitor_thread = threading.Thread(target=self._collect_data_loop, args=(interval,))
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _collect_data_loop(self, interval):
        """
        采集全量核心性能数据
        timestamp/record_time 仅做时间记录，不会参与任何平均值、图表计算
        """
        while self.is_running:
            # ========== 新增超多实用性能指标 ==========
            mock_data = {
                # 时间相关：只记录，**绝不统计、不画曲线**
                "timestamp": time.time(),
                "record_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

                # 核心性能指标（自动统计均值/最大/最小、自动进图表）
                "cpu_usage": round(time.time() % 100, 2),          # CPU使用率 %
                "memory_mb": round(100 + time.time() % 50, 2),     # 内存占用 MB
                "fps": round(55 + time.time() % 10, 1),            # 实时帧率 FPS
                "gpu_usage": round(time.time() % 80, 2),           # GPU使用率 %
                "battery_level": round(60 + time.time() % 40, 1),  # 手机电量 %
                "network_rx_kb": round(time.time() % 1024, 2),     # 下行流量 KB/s
                "network_tx_kb": round(time.time() % 512, 2),      # 上行流量 KB/s
                "jank_count": round(time.time() % 5, 0),           # 卡顿次数
                "frame_jitter": round(time.time() % 8, 2)          # 帧率抖动值
            }
            self.data_records.append(mock_data)
            time.sleep(interval)

    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            print("✅ 性能监控线程已正常停止")

    def generate_report(self, output_dir="./reports"):
        """
        生成双版本报告：
        1. JSON原始数据报告（程序解析用）
        2. HTML可视化图文报告（带统计表格+多曲线趋势图）
        ✅ timestamp/record_time 自动排除统计和图表，只做展示
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        ts = int(time.time())
        json_filename = f"perf_report_{ts}.json"
        html_filename = f"perf_report_{ts}.html"
        json_filepath = os.path.join(output_dir, json_filename)
        html_filepath = os.path.join(output_dir, html_filename)

        total_samples = len(self.data_records)

        # ========== 核心：只筛选性能数值字段，自动排除时间字段 ==========
        stats = {}
        num_fields = []
        if total_samples > 0:
            # 只拿数字类型 + 不在排除列表里的字段
            num_fields = [
                k for k in self.data_records[0]
                if isinstance(self.data_records[0][k], (int, float)) and k not in self.exclude_stat_fields
            ]
            # 自动计算每项性能：平均值/最大值/最小值/采样数
            for key in num_fields:
                values = [
                    r[key] for r in self.data_records
                    if key in r and isinstance(r[key], (int, float))
                ]
                if values:
                    stats[key] = {
                        "avg": round(sum(values) / len(values), 2),
                        "max": round(max(values), 2),
                        "min": round(min(values), 2),
                        "count": len(values)
                    }

        # 组装JSON报告结构
        report_data = {
            "report_info": {
                "report_name": "APP自动化全量性能测试报告",
                "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "package_name": self.package_name,
                "device_serial": self.device_serial,
                "total_samples": total_samples,
                "exclude_fields_note": "timestamp、record_time仅时间记录，不参与性能统计"
            },
            "data_summary_statistics": stats,
            "original_detail_data": self.data_records
        }

        # 保存JSON
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=4)

        # ========== HTML图表数据拼接（只拼性能指标，不含时间） ==========
        chart_labels = [str(i + 1) for i in range(total_samples)]
        chart_datasets = ""
        color_list = [
            "#ff6384", "#36a2eb", "#4bc0c0", "#9966ff", "#ff9f40",
            "#ffcd56", "#c9cbcf", "#8e5ea2", "#2ecc71"
        ]
        for idx, field in enumerate(num_fields):
            val_list = [str(r.get(field, 0)) for r in self.data_records]
            border_color = color_list[idx % len(color_list)]
            chart_datasets += f"""
            {{
                label: '{field}',
                data: [{','.join(val_list)}],
                borderColor: '{border_color}',
                backgroundColor: '{border_color}33',
                borderWidth: 2,
                tension: 0.3,
                fill: false
            }},
            """

        # 统计汇总表格HTML
        stat_html = ""
        if stats:
            stat_html += "<table border='1' cellpadding='8' cellspacing='0' width='100%'>"
            stat_html += "<tr style='background:#f0f7ff'><th>性能指标名称</th><th>平均值</th><th>最大值</th><th>最小值</th><th>有效采样次数</th></tr>"
            for k, v in stats.items():
                stat_html += f"""
                <tr align='center'>
                    <td>{k}</td>
                    <td>{v['avg']}</td>
                    <td>{v['max']}</td>
                    <td>{v['min']}</td>
                    <td>{v['count']}</td>
                </tr>
                """
            stat_html += "</table>"
        else:
            stat_html += "<p>暂无性能统计数据，请先执行性能采集</p>"

        # 高颜值HTML完整模板
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>APP全量性能可视化测试报告</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
    body {{font-family: "Microsoft Yahei",sans-serif; margin: 20px; background: #f9fafc;}}
    .box {{background: #fff; padding:20px; border-radius:8px; box-shadow:0 0 8px #eee; margin-bottom:20px;}}
    h2 {{color:#2c3e50; font-size:20px;}}
    p {{font-size:15px; color:#333;}}
    table {{font-size:14px; color:#333; text-align:center;}}
</style>
</head>
<body>
    <div class="box">
        <h2>📱 测试基础信息</h2>
        <p><b>测试应用包名：</b>{self.package_name}</p>
        <p><b>测试设备序列号：</b>{self.device_serial}</p>
        <p><b>报告生成时间：</b>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><b>性能采样总次数：</b>{total_samples}</p>
        <p style="color:#999;font-size:13px;">💡 时间戳字段仅做记录，不参与任何性能统计与趋势绘图</p>
    </div>

    <div class="box">
        <h2>📊 全量性能数据统计汇总表</h2>
        {stat_html}
    </div>

    <div class="box">
        <h2>📈 多指标性能趋势折线图</h2>
        <canvas id="perfChart" height="300"></canvas>
    </div>

<script>
const ctx = document.getElementById('perfChart').getContext('2d');
new Chart(ctx, {{
    type: 'line',
    data: {{
        labels: [{','.join(chart_labels)}],
        datasets: [{chart_datasets}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            title: {{display:true, text:'CPU/内存/FPS/GPU/电量/流量 全指标趋势变化图', fontsize:16}},
            legend: {{display:true, position:'bottom'}}
        }},
        scales: {{
            x: {{title:{{display:true, text:'采样次数'}}}},
            y: {{title:{{display:true, text:'对应指标数值'}}}}
        }}
    }}
}});
</script>
</body>
</html>
        """

        # 写入HTML报告
        with open(html_filepath, 'w', encoding='utf-8') as f:
            f.write(html_template)

        print("✅ 已生成JSON原始数据报告：", json_filepath)
        print("✅ 已生成HTML可视化图表报告：", html_filepath)
        return json_filepath
