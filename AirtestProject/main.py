from airtest.core.api import *
from startUp.app_launcher import AppLauncher
from checkTraditionWay.check_tradition import CheckTradition
from config import ENABLE_APP_LAUNCH,DEVICE_SN

if __name__ == "__main__":
    # 连接设备
    auto_setup(__file__)
    device_sn = DEVICE_SN
    connect_device(f"Android://127.0.0.1:5037/{device_sn}")
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


    # 登录流程
        