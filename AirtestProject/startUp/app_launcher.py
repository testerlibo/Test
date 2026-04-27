# -*- coding: utf-8 -*-
import logging
from airtest.core.api import device, sleep
from config import PACKAGE_NAME, APP_START_TIMEOUT

# 关闭 adb 日志
logging.getLogger("airtest.core.android.adb").setLevel(logging.ERROR)

class AppLauncher:
    def __init__(self, package_name=PACKAGE_NAME):
        self.package_name = package_name
        self.dev = device()  # 直接获取已连接的设备，不自己连

    def start_app_safely(self):
        """安全启动APP：检查前台 → 关闭 → 启动 → 等待"""
        try:
            current_activity = self.dev.get_top_activity()

            if self.package_name in current_activity:
                print("✅ APP 已在前台")
                return True

            print(f"🔄 重启应用...")
            self.dev.stop_app(self.package_name)
            sleep(1)
            self.dev.start_app(self.package_name)
            sleep(APP_START_TIMEOUT)
            return True

        except Exception as e:
            print(f"❌ 启动失败: {str(e)}")
            return False

    def is_app_running(self):
        """检查APP是否在前台运行"""
        try:
            return self.package_name in self.dev.get_top_activity()
        except:
            return False

    def launch_and_verify(self):
        """启动 + 验证"""
        return self.start_app_safely() and self.is_app_running()