# NewsTracking

Twitter → 钉钉 实时消息推送系统，支持 A 股关键词特别提醒。

## 功能

- 每分钟/每 5 分钟轮询 Twitter 作者的推文和回复
- 全部推文实时推送至钉钉群机器人
- A 股相关消息自动标注 🔴【A股相关】醒目提醒
- 自动去重，同一条绝不推送两次
- 支持同时跟踪多个 Twitter 作者
- 可配置的 A 股关键词列表
- Docker 部署 / GitHub Actions 免服务器运行

## 工作原理

```
Nitter RSS → Fetcher 获取推文 → Matcher 关键词匹配 → Pusher 钉钉推送 → Store 去重
```

通过 [Nitter](https://github.com/zedeus/nitter) 的 RSS 接口获取 Twitter 数据，无需 Twitter API 付费订阅。

## 快速开始

### 方式一：GitHub Actions（推荐，无需服务器）

1. Fork 本仓库
2. 在 `Settings → Secrets and variables → Actions` 中添加 Secret：
   - 名称：`DINGTALK_WEBHOOK_URL`
   - 值：你的钉钉机器人 Webhook 地址
3. 编辑 `config.yaml` 修改要跟踪的作者和关键词
4. GitHub Actions 会自动每 5 分钟运行一次

手动触发：`Actions → Twitter to DingTalk Tracker → Run workflow`

### 方式二：Docker 运行

```bash
# 1. 编辑 config.yaml，填入钉钉 Webhook URL
# 2. 启动
docker compose up -d

# 查看日志
docker compose logs -f
```

### 方式三：本地运行

```bash
# 1. 安装
pip install -r requirements.txt

# 2. 设置钉钉 Webhook（二选一）
# 方式 A：环境变量（推荐，不泄露密钥）
set DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=你的token

# 方式 B：直接写在 config.yaml 里

# 3. 启动（持续运行模式，每分钟轮询）
python -m src.main config.yaml

# 或者单次运行模式
python -m src.main config.yaml --once
```

## 配置说明

编辑 `config.yaml`：

```yaml
# 要跟踪的作者列表（可添加多个）
authors:
  - username: "aleabitoreddit"    # Twitter 用户名
    display_name: "Ale Abit"      # 钉钉里显示的名称

# Nitter 实例（按优先级排列，挂了自动切换）
nitter_instances:
  - "https://nitter.net"
  - "https://nitter.privacydev.net"
  - "https://nitter.poast.org"

# 钉钉配置（推荐使用环境变量 DINGTALK_WEBHOOK_URL 替代）
dingtalk:
  webhook_url: ""

# A 股关键词列表（推文内容包含任一关键词即标记）
a_stock_keywords:
  - "A股"
  - "上证"
  - "深证"
  - "沪指"
  - "深成指"
  - "创业板"
  - "科创板"
  - "北向"
  - "南向"
  - "券商"
  - "涨停"
  - "跌停"
  - "沪深"
  - "中证"
  - "IPO"
  - "证监会"
  - "印花税"
  - "量化"

# 轮询间隔（秒），GitHub Actions 中此值无效
poll_interval_seconds: 60

# SQLite 数据库路径
database_path: "data/tweets.db"
```

### 添加新的跟踪作者

在 `authors` 列表中添加：

```yaml
authors:
  - username: "aleabitoreddit"
    display_name: "Ale Abit"
  - username: "another_user"
    display_name: "另一个人"
```

### 修改 A 股关键词

直接编辑 `a_stock_keywords` 列表，增删关键词即可。下次轮询自动生效。

## 钉钉消息格式

**普通推文：**
```
📢 @Ale Abit 新推文

> 推文内容...

🔗 https://x.com/aleabitoreddit/status/1234567890
🕐 2026-06-06 14:30:00
```

**A 股相关推文：**
```
🔴【A股相关】📢 @Ale Abit 新推文

> 这条推文提到了A股市场...

🔗 https://x.com/aleabitoreddit/status/1234567890
🕐 2026-06-06 14:30:00
```

**回复推文：**
```
💬 @Ale Abit 的回复

> 回复内容...

🔗 https://x.com/aleabitoreddit/status/1234567890
🕐 2026-06-06 15:00:00
```

## 获取钉钉 Webhook URL

1. 打开钉钉，进入目标群聊
2. 点击右上角 `...` → `智能群助手` → `添加机器人`
3. 选择 `自定义机器人`
4. 安全设置选择 `自定义关键词`，填入 `A股`（可选）
5. 复制 Webhook URL

## 常见问题

### Nitter 实例全部不可用怎么办？

编辑 `config.yaml`，从 [Nitter 实例列表](https://github.com/isarantopoulos/Nitter/tree/master#instances) 找到可用的新实例，添加到 `nitter_instances` 中。

### GitHub Actions 运行频率能改吗？

可以，编辑 `.github/workflows/run.yml` 中的 `cron` 表达式：
- `*/5 * * * *` = 每 5 分钟
- `*/10 * * * *` = 每 10 分钟
- GitHub 最短间隔为 5 分钟

### 为什么本地运行和 GitHub Actions 运行间隔不同？

- 本地/Docker 持续运行模式使用 `poll_interval_seconds`（默认 60 秒）
- GitHub Actions 的 cron 控制运行频率（默认 5 分钟）
- `--once` 模式下 `poll_interval_seconds` 无效

### 会不会把历史推文全部推送一遍？

不会。首次运行只记录不推送历史推文，后续通过 SQLite 数据库去重，同一条推文绝不重复推送。

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行指定模块测试
pytest tests/test_fetcher.py -v
```

## 项目结构

```
NewsTracking/
├── config.yaml              # 配置文件
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── docker-compose.yaml
├── .github/workflows/run.yml  # GitHub Actions 工作流
├── src/
│   ├── main.py                # 入口
│   ├── config.py              # 配置加载
│   ├── fetcher.py             # Nitter RSS 获取
│   ├── matcher.py             # A股关键词匹配
│   ├── pusher.py              # 钉钉推送
│   ├── scheduler.py           # 调度器
│   └── store.py               # SQLite 去重
├── data/                      # 运行时数据
└── tests/                     # 测试
```
