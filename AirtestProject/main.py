# -*- coding: utf-8 -*-
from airtest.core.api import *
from perfTest.perf_croe import PerformanceMonitor
from startUp.app_launcher import AppLauncher
from checkTraditionWay.check_tradition import CheckTradition
from config import ENABLE_APP_LAUNCH, DEVICE_SN, ENABLE_PERF_CORE, PACKAGE_NAME

if __name__ == "__main__":
    perfmon = None  # 初始化性能监控避免报错
    # 连接设备
    auto_setup(__file__)
    connect_device(f"Android://127.0.0.1:5037/{DEVICE_SN}")
    print("✅ 设备已连接")

    # 启动 app
    if ENABLE_APP_LAUNCH:
        launcher = AppLauncher()
        if launcher.launch_and_verify():
            print("🎉 【启动成功】APP 已正常运行！")
        else:
            print("❌ 启动失败，请检查设备或包名")
        # 检查登录页面繁体转换
        checker = CheckTradition()
        errors = checker.check_current_screen()
    else:
        print("ℹ️ APP启动模块已关闭")

    # 启动 性能监控
    if ENABLE_PERF_CORE:
        print("ℹ️ 启动性能监控")
        perfmon = PerformanceMonitor(package_name= PACKAGE_NAME, device_serial= DEVICE_SN)
        perfmon.start_monitoring(interval=1.0)
    else:
        print("ℹ️ 性能监控模块已关闭")

    # 登录流程

    # 关闭 性能监控
    if perfmon:
        time.sleep(30)
        perfmon.stop_monitoring()
        perfmon.generate_report()
