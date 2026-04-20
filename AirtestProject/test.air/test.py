# -*- coding: utf-8 -*-
from airtest.core.api import *

# 连接设备
auto_setup(__file__)
device_sn = "bbafe05b0604"
connect_device(f"Android://127.0.0.1:5037/{device_sn}")
print("✅ 设备已连接")

