# -*- coding: utf-8 -*-
import os
import sys
import shutil

def refresh_windows_env_path():
    if sys.platform != "win32":
        return

    try:
        import winreg
        paths = []

        # 系统PATH
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment") as reg:
                paths.append(winreg.QueryValueEx(reg, "PATH")[0])
        except Exception:
            pass

        # 用户PATH
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as reg:
                paths.append(winreg.QueryValueEx(reg, "PATH")[0])
        except Exception:
            pass

        # ==========================================
        # ✅ 只追加，不覆盖！保护原有环境（PaddleOCR 不报错）
        # ==========================================
        os.environ["PATH"] += os.pathsep + os.pathsep.join(paths)

    except Exception:
        pass


def check_adb_available() -> bool:
    return shutil.which("adb") is not None