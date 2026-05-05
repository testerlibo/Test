# APITest

基于大模型生成用例、自动请求游戏登录相关 HTTP 接口，并对返回结果做 **normal / negative** 预期判定，最后输出控制台与 `report.txt` / `report.json` / `report.html` 报告。

## 环境要求

- **Python 3.9+**（开发自测使用 3.9）
- 能访问配置中的 **业务 API 地址** 与 **大模型 OpenAI 兼容接口**（如阿里云 DashScope 等）

## 依赖说明

### 运行主程序（`python main.py`）

| 包 | 版本约束 | 用途 |
|----|-----------|------|
| `requests` | `>=2.31.0,<3` | HTTP 调用业务接口与大模型 Chat API |

其余均为 Python **标准库**（如 `json`、`datetime` 等），无需单独安装。

### 单元测试（可选）

| 包 | 版本约束 | 用途 |
|----|-----------|------|
| `pytest` | `>=8.0.0` | 运行 `tests/` 下的自动化测试 |

## 安装

在项目根目录（本 README 所在目录）执行：

```bash
pip install "requests>=2.31.0,<3"
```

若需要跑单元测试：

```bash
pip install "requests>=2.31.0,<3" "pytest>=8.0.0"
```

也可使用等价的一条命令：

```bash
pip install "requests>=2.31.0,<3" "pytest>=8.0.0"
```

## 配置（`config.py`）

| 配置项 | 说明 |
|--------|------|
| `BASE_URL` | 业务 API 根地址（路径会与 `API_INFO` 中的 `url` 拼接） |
| `AI_CONFIG` | 大模型：`api_key`、`base_url`、`model`、`temperature`（OpenAI 兼容 `/chat/completions`） |
| `API_INFO` | 各接口的 `name`、`method`、`url`、`default` 默认请求体 |
| `HEADERS` | 公共请求头 |
| `CLIENT_META` | 客户端元信息，可在登录等默认参数中复用 |

**安全提示**：请勿将真实密钥、账号密码提交到公开仓库；建议使用环境变量或本地未跟踪的配置文件，由应用读取后再写入内存（当前仓库为示例结构，请自行加固）。

## 使用方式

### 执行接口测试

```bash
python main.py
```

流程概要：

1. 使用 `acc_login` 登录并获取 token，后续请求携带 `Authorization: Bearer <token>`。
2. 遍历 `API_INFO` 中除登录外的接口；对每个接口请求大模型生成 **JSON 用例数组**。
3. **解析**（`core/case_parser`）后 **归一化**（`core/case_bundle`）：每个接口固定 **1 条 normal + 4 条 negative**，不足时用内置模板补足。
4. 发起请求，用 `core/result_judge` 判定是否符合预期；汇总到报告模块 `core/report`。

### 运行单元测试

在项目根目录：

```bash
python -m pytest tests/ -v
```

## 输出文件

运行成功后可能在项目根目录生成：

- `report.txt` — 文本报告  
- `report.json` — JSON 报告  
- `report.html` — HTML 报告  

如需纳入版本管理或分享，注意脱敏（token、账号等）。

## 目录结构（概要）

```
APITest/
├── main.py              # 入口
├── config.py            # 环境与接口配置
├── README.md
├── core/
│   ├── api_client.py    # HTTP 客户端
│   ├── ai_agent.py      # 大模型生成用例与分析文案
│   ├── case_parser.py   # 解析 AI 返回（JSON / 旧版「名称|参数」）
│   ├── case_bundle.py   # 固定 1 normal + 4 negative
│   ├── result_judge.py  # 预期判定（kind + code）
│   └── report.py        # 报告生成
└── tests/               # pytest 单元测试
```

## 常见问题

- **某接口始终只有内置补足用例**：多为大模型返回非合法 JSON 数组或字段校验失败，控制台会有「解析/归一化」提示；可检查 `config` 中默认参数与模型输出格式。

---

如对依赖版本有严格复现需求，可在安装后执行 `pip freeze > requirements-lock.txt` 自行生成锁定文件（本仓库不再维护单独的 `require.txt`）。
