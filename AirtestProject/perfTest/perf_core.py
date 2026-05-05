# -*- coding: utf-8 -*-
"""通过 ADB 采集 Android 端真实性能数据（内存、CPU、电量、流量、帧率/卡顿）。"""
from __future__ import annotations
import html
import json
import os
import re
import shutil
import subprocess
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


class PerformanceMonitor:
    def __init__(self, package_name: str, device_serial: str):
        self.package_name = package_name
        self.device_serial = device_serial
        self.is_running = False
        self.data_records: List[Dict[str, Any]] = []
        self.monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.exclude_stat_fields = ["timestamp", "record_time"]

        self.last_total_rx = 0.0
        self.last_total_tx = 0.0
        self._flow_initialized = False

        # CPU：/proc/<pid>/stat 与 /proc/stat 双采样
        self._prev_proc_ticks: Optional[int] = None
        self._prev_total_ticks: Optional[int] = None

        # 帧率：gfxinfo 累计帧数差分
        self._prev_gfx_frames: Optional[int] = None
        self._prev_janky: Optional[int] = None

        self._app_uid: Optional[int] = None

    # ---------- ADB ----------
    def _adb_prefix(self) -> List[str]:
        return ["adb", "-s", self.device_serial]

    def _shell(self, *shell_args: str, timeout: float = 12.0) -> str:
        cmd = self._adb_prefix() + ["shell"] + list(shell_args)
        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            return (r.stdout or "") + (r.stderr or "")
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError, Exception):
            return ""

    def _ensure_adb(self) -> bool:
        return shutil.which("adb") is not None

    def is_device_online(self) -> bool:
        try:
            r = subprocess.run(
                self._adb_prefix() + ["get-state"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=8.0,
            )
            return (r.stdout or "").strip() == "device"
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    # ---------- 进程 / UID ----------
    def _get_main_pid(self) -> Optional[int]:
        out = self._shell("pidof", self.package_name, timeout=5.0).strip()
        if not out:
            return None
        parts = out.split()
        try:
            return int(parts[0])
        except (ValueError, IndexError):
            return None

    def _get_app_uid(self) -> Optional[int]:
        if self._app_uid is not None:
            return self._app_uid
        out = self._shell("dumpsys", "package", self.package_name, timeout=15.0)
        for line in out.splitlines():
            if "userId=" in line:
                m = re.search(r"userId=(\d+)", line)
                if m:
                    self._app_uid = int(m.group(1))
                    return self._app_uid
        return None

    # ---------- 内存（PSS） ----------
    def _get_memory_pss_mb(self) -> float:
        out = self._shell("dumpsys", "meminfo", self.package_name, timeout=15.0)
        # 常见行： TOTAL PSS:    123456  TOTAL RSS: ...
        for pattern in (
            r"TOTAL\s+PSS:\s*([\d,]+)",
            r"Total\s+PSS:\s*([\d,]+)\s*kB",
            r"Total\s+PSS:\s*([\d,]+)",
        ):
            m = re.search(pattern, out, re.IGNORECASE)
            if m:
                kb = int(m.group(1).replace(",", ""))
                return round(kb / 1024.0, 2)
        # 旧格式：  TOTAL   123456  （KB）
        for line in out.splitlines():
            if line.strip().startswith("TOTAL") and "PSS" not in line.upper():
                parts = line.split()
                for i, p in enumerate(parts):
                    if p.isdigit() and i > 0:
                        try:
                            val = int(p.replace(",", ""))
                            if val > 1000:
                                return round(val / 1024.0, 2)
                        except ValueError:
                            pass
        return 0.0

    # ---------- CPU ----------
    @staticmethod
    def _parse_pid_stat_utime_stime(content: str) -> Optional[Tuple[int, int]]:
        """/proc/<pid>/stat：字段14、15为 utime, stime。"""
        s = content.strip()
        try:
            rp = s.rindex(")")
            rest = s[rp + 2 :].split()
            utime, stime = int(rest[11]), int(rest[12])
            return utime, stime
        except (ValueError, IndexError):
            return None

    def _get_cpu_usage_percent(self, pid: Optional[int]) -> float:
        if not pid:
            return 0.0
        proc_out = self._shell("cat", f"/proc/{pid}/stat", timeout=5.0)
        cpu_out = self._shell("cat", "/proc/stat", timeout=5.0)
        pid_ts = self._parse_pid_stat_utime_stime(proc_out)
        cpu_line = cpu_out.splitlines()[0] if cpu_out else ""
        parts = cpu_line.split()
        if not parts or parts[0] != "cpu" or pid_ts is None:
            return 0.0
        try:
            jiffies = [int(x) for x in parts[1:]]
        except ValueError:
            return 0.0
        proc_ticks = pid_ts[0] + pid_ts[1]
        total_ticks = sum(jiffies)

        if self._prev_proc_ticks is None or self._prev_total_ticks is None:
            self._prev_proc_ticks = proc_ticks
            self._prev_total_ticks = total_ticks
            return 0.0

        d_proc = proc_ticks - self._prev_proc_ticks
        d_total = total_ticks - self._prev_total_ticks
        self._prev_proc_ticks = proc_ticks
        self._prev_total_ticks = total_ticks

        if d_total <= 0:
            return 0.0
        # 多核下进程可超过单核 100%，不强行 cap
        return round(100.0 * d_proc / d_total, 2)

    # ---------- 电量 ----------
    def _get_battery_level(self) -> float:
        out = self._shell("dumpsys", "battery", timeout=8.0)
        m = re.search(r"level:\s*(\d+)", out, re.IGNORECASE)
        if m:
            return float(m.group(1))
        return 0.0

    # ---------- 流量：优先 uid_stat，不可用时 dumpsys netstats 回退 ----------
    @staticmethod
    def _last_numeric_line(text: str) -> Optional[str]:
        for ln in reversed([x.strip() for x in (text or "").splitlines() if x.strip()]):
            s = ln.replace(",", "")
            if s.isdigit() or (s.count(".") == 1 and s.replace(".", "").isdigit()):
                return s
        return None

    def _try_uid_stat_rx_tx_mb(self, uid: int) -> Optional[Tuple[float, float]]:
        base = f"/proc/uid_stat/{uid}"
        raw_rcv = self._shell("cat", f"{base}/tcp_rcv", timeout=3.0)
        raw_snd = self._shell("cat", f"{base}/tcp_snd", timeout=3.0)
        combined = raw_rcv + raw_snd
        if "No such file" in combined or "Invalid argument" in combined:
            return None
        if "Permission denied" in combined:
            return None
        rcv_s = self._last_numeric_line(raw_rcv)
        snd_s = self._last_numeric_line(raw_snd)
        if rcv_s is None and snd_s is None:
            return None
        try:
            rx = float(rcv_s) if rcv_s is not None else 0.0
            tx = float(snd_s) if snd_s is not None else 0.0
        except ValueError:
            return None
        return round(rx / (1024.0 * 1024.0), 4), round(tx / (1024.0 * 1024.0), 4)

    def _get_netstats_rx_tx_mb(self, uid: int) -> Optional[Tuple[float, float]]:
        out = self._shell("dumpsys", "netstats", timeout=10.0)
        if not out.strip():
            return None
        patterns = (
            re.compile(
                rf"(?is)uid[= ]*{uid}\b[\s\S]{{0,2500}}?total[\s\S]{{0,400}}?(\d+)\s+bytes[\s\S]{{0,400}}?(\d+)\s+bytes"
            ),
            re.compile(
                rf"(?is)NetworkStatsSummary[\s\S]{{0,8000}}?uid[= ]*{uid}\b[\s\S]{{0,1200}}?rb[= ](\d+)[\s\S]{{0,300}}?tb[= ](\d+)"
            ),
            re.compile(
                rf"(?is)ident\s*\[[^\]]*{uid}[^\]]*\][\s\S]{{0,600}}?rb[= ](\d+)[\s\S]{{0,200}}?tb[= ](\d+)"
            ),
        )
        for pat in patterns:
            m = pat.search(out)
            if m:
                try:
                    rx_b = int(m.group(1))
                    tx_b = int(m.group(2))
                except (ValueError, IndexError):
                    continue
                return round(rx_b / (1024.0 * 1024.0), 4), round(
                    tx_b / (1024.0 * 1024.0), 4
                )
        return None

    def _get_flow_data(self) -> Tuple[float, float]:
        uid = self._get_app_uid()
        if uid is None:
            return 0.0, 0.0
        uid_mb = self._try_uid_stat_rx_tx_mb(uid)
        if uid_mb is not None:
            return uid_mb[0], uid_mb[1]
        ns = self._get_netstats_rx_tx_mb(uid)
        if ns is not None:
            return ns[0], ns[1]
        return 0.0, 0.0

    # ---------- Gfx：帧率、卡顿增量、帧耗时抖动（90th-50th ms） ----------
    def _parse_gfxinfo(self) -> Tuple[Optional[int], Optional[int], float]:
        out = self._shell("dumpsys", "gfxinfo", self.package_name, timeout=12.0)
        frames = None
        m = re.search(r"Total frames rendered:\s*(\d+)", out)
        if m:
            frames = int(m.group(1))
        janky = None
        m2 = re.search(r"Janky frames.*?:\s*(\d+)\s*/\s*(\d+)", out)
        if m2:
            janky = int(m2.group(1))
        else:
            m3 = re.search(r"Janky frames.*?:\s*(\d+)\s*\(", out)
            if m3:
                janky = int(m3.group(1))
        p50 = p90 = None
        m50 = re.search(r"50th percentile:\s*([\d.]+)\s*ms", out, re.IGNORECASE)
        m90 = re.search(r"90th percentile:\s*([\d.]+)\s*ms", out, re.IGNORECASE)
        if m50 and m90:
            try:
                p50 = float(m50.group(1))
                p90 = float(m90.group(1))
            except ValueError:
                pass
        jitter = round(p90 - p50, 2) if p50 is not None and p90 is not None else 0.0
        return frames, janky, jitter

    def _fps_and_jank_delta(
        self, interval: float
    ) -> Tuple[float, float, float]:
        frames, janky, jitter = self._parse_gfxinfo()
        fps = 0.0
        jank_delta = 0.0
        if frames is not None and self._prev_gfx_frames is not None and interval > 0:
            df = frames - self._prev_gfx_frames
            if df >= 0:
                fps = round(df / interval, 2)
        if janky is not None and self._prev_janky is not None:
            dj = janky - self._prev_janky
            jank_delta = float(dj) if dj >= 0 else 0.0
        if frames is not None:
            self._prev_gfx_frames = frames
        if janky is not None:
            self._prev_janky = janky
        return fps, jank_delta, jitter

    # ---------- 采集循环 ----------
    def start_monitoring(self, interval: float = 1.0) -> None:
        if self.monitor_thread and self.monitor_thread.is_alive():
            print("⚠️ 性能监控已在运行，请先调用 stop_monitoring() 再启动")
            return
        if not self._ensure_adb():
            print("❌ 未找到 adb，请安装 Android SDK platform-tools 并加入 PATH")
            return
        if not self.is_device_online():
            print("❌ 设备未在线（adb get-state 非 device），请检查连接与序列号")
            return
        self.is_running = True
        with self._lock:
            self.data_records.clear()
        self.last_total_rx = 0.0
        self.last_total_tx = 0.0
        self._flow_initialized = False
        self._prev_proc_ticks = None
        self._prev_total_ticks = None
        self._prev_gfx_frames = None
        self._prev_janky = None
        self.monitor_thread = threading.Thread(
            target=self._collect_data_loop,
            args=(interval,),
            daemon=True,
        )
        self.monitor_thread.start()
        print(f"✅ 性能监控已启动 | 采样间隔：{interval}s")

    def _collect_data_loop(self, interval: float) -> None:
        while self.is_running:
            t0 = time.time()
            pid = self._get_main_pid()

            current_total_rx, current_total_tx = self._get_flow_data()
            if not self._flow_initialized:
                current_rx_kb = 0.0
                current_tx_kb = 0.0
                self._flow_initialized = True
            else:
                dr = (current_total_rx - self.last_total_rx) * 1024.0
                dt = (current_total_tx - self.last_total_tx) * 1024.0
                current_rx_kb = round(max(0.0, dr) / max(interval, 1e-6), 2)
                current_tx_kb = round(max(0.0, dt) / max(interval, 1e-6), 2)

            self.last_total_rx = max(self.last_total_rx, current_total_rx)
            self.last_total_tx = max(self.last_total_tx, current_total_tx)

            mem_mb = self._get_memory_pss_mb() if pid else 0.0
            cpu_usage = self._get_cpu_usage_percent(pid)
            battery = self._get_battery_level()

            fps, jank_delta, frame_jitter = self._fps_and_jank_delta(interval)

            record: Dict[str, Any] = {
                "timestamp": time.time(),
                "record_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cpu_usage": cpu_usage,
                "memory_mb": mem_mb,
                "fps": fps,
                "battery_level": battery,
                "jank_count": jank_delta,
                "frame_jitter": frame_jitter,
                "total_rx_mb": round(self.last_total_rx, 4),
                "total_tx_mb": round(self.last_total_tx, 4),
                "current_rx_kb": current_rx_kb,
                "current_tx_kb": current_tx_kb,
            }
            with self._lock:
                self.data_records.append(record)

            elapsed = time.time() - t0
            sleep_left = interval - elapsed
            if sleep_left > 0:
                time.sleep(sleep_left)

    def stop_monitoring(self) -> None:
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=8)
            if self.monitor_thread.is_alive():
                print("⚠️ 性能监控线程未在超时内结束，后台可能仍在收尾")
            else:
                print("✅ 性能监控线程已正常停止")

    def generate_report(self, output_dir: str = "./reports") -> str:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with self._lock:
            snapshot = list(self.data_records)

        ts = int(time.time())
        json_filename = f"perf_report_{ts}.json"
        html_filename = f"perf_report_{ts}.html"
        json_filepath = os.path.join(output_dir, json_filename)
        html_filepath = os.path.join(output_dir, html_filename)

        total_samples = len(snapshot)

        stats: Dict[str, Any] = {}
        num_fields: List[str] = []
        if total_samples > 0:
            num_fields = [
                k
                for k in snapshot[0]
                if isinstance(snapshot[0][k], (int, float))
                and k not in self.exclude_stat_fields
            ]
            for key in num_fields:
                values = [
                    r[key]
                    for r in snapshot
                    if key in r and isinstance(r[key], (int, float))
                ]
                if values:
                    stats[key] = {
                        "avg": round(sum(values) / len(values), 2),
                        "max": round(max(values), 2),
                        "min": round(min(values), 2),
                        "count": len(values),
                    }

        report_data = {
            "report_info": {
                "report_name": "APP 自动化性能测试报告（ADB 实采）",
                "generate_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "package_name": self.package_name,
                "device_serial": self.device_serial,
                "total_samples": total_samples,
                "data_source": (
                    "内存:dumpsys meminfo PSS; CPU:/proc 差分; 电量:dumpsys battery; "
                    "流量:优先 /proc/uid_stat/<uid>/tcp_rcv|tcp_snd，不可用时尝试 dumpsys netstats; "
                    "帧率/卡顿:dumpsys gfxinfo 差分"
                ),
                "metrics_notes": (
                    "current_rx_kb / current_tx_kb 表示该采样周期内的下行/上行速率（KB/s）；"
                    "jank_count 为相邻两次 gfxinfo 采样间的卡顿帧增量；"
                    "CPU 为多核 jiffies 占比，可超过 100%。"
                ),
            },
            "data_summary_statistics": stats,
            "original_detail_data": snapshot,
        }

        with open(json_filepath, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=4)

        chart_labels = [str(i + 1) for i in range(total_samples)]
        chart_labels_js = ",".join(json.dumps(lbl) for lbl in chart_labels)
        chart_datasets = ""
        color_list = [
            "#ff6384",
            "#36a2eb",
            "#4bc0c0",
            "#9966ff",
            "#ff9f40",
            "#ffcd56",
            "#c9cbcf",
            "#8e5ea2",
            "#2ecc71",
            "#e74c3c",
            "#1abc9c",
            "#34495e",
        ]
        for idx, field in enumerate(num_fields):
            val_list = [str(r.get(field, 0)) for r in snapshot]
            border_color = color_list[idx % len(color_list)]
            label_js = json.dumps(field, ensure_ascii=False)
            chart_datasets += f"""
            {{
                label: {label_js},
                data: [{",".join(val_list)}],
                borderColor: '{border_color}',
                backgroundColor: '{border_color}33',
                borderWidth: 2,
                tension: 0.3,
                fill: false
            }},
            """

        stat_html = ""
        if stats:
            stat_html += (
                "<table border='1' cellpadding='8' cellspacing='0' width='100%'>"
            )
            stat_html += "<tr style='background:#f0f7ff'><th>性能指标名称</th><th>平均值</th>"
            stat_html += "<th>最大值</th><th>最小值</th><th>有效采样次数</th></tr>"
            for k, v in stats.items():
                k_esc = html.escape(str(k), quote=False)
                stat_html += f"""
                <tr align='center'>
                    <td>{k_esc}</td>
                    <td>{v['avg']}</td>
                    <td>{v['max']}</td>
                    <td>{v['min']}</td>
                    <td>{v['count']}</td>
                </tr>
                """
            stat_html += "</table>"
        else:
            stat_html += "<p>暂无性能统计数据，请先执行性能采集</p>"

        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>APP 性能可视化报告（ADB）</title>
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
        <p><b>测试应用包名：</b>{html.escape(self.package_name, quote=False)}</p>
        <p><b>测试设备序列号：</b>{html.escape(self.device_serial, quote=False)}</p>
        <p><b>报告生成时间：</b>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p><b>性能采样总次数：</b>{total_samples}</p>
        <p style="color:#555;font-size:13px;">数据来源：ADB 实采；流量优先 uid_stat，不可用时尝试 netstats；current_rx/tx_kb 为 KB/s；jank_count 为采样间隔内卡顿帧增量；首帧 CPU 常为 0（基线）。</p>
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
        labels: [{chart_labels_js}],
        datasets: [{chart_datasets}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            title: {{display:true, text:'CPU/内存/FPS/电量/流量/卡顿 趋势', font: {{size: 16}}}},
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

        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(html_template)

        print("✅ 已生成JSON原始数据报告：", json_filepath)
        print("✅ 已生成HTML可视化图表报告：", html_filepath)
        return json_filepath
