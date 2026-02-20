# 🌍 全球资产监控系统 - 项目交付文档

## 📦 项目概览

感谢您选择全球资产监控系统！这是一个**生产级、高度模块化**的监控平台，专为追踪汇率、电商折扣及机票价格而设计。

---

## 🎯 核心特性一览

### ✅ 已实现功能

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| 💱 **汇率监控** | ✅ 完整 | 180天Z-Score模型 + 4%硬性门槛 |
| 🛒 **京东自营监控** | ✅ 完整 | H5移动端优化 + 反爬加固 |
| 🛍️ **Amazon监控** | ✅ 完整 | 多区域支持 + ASIN/URL监控 |
| ✈️ **机票监控** | 🔧 框架 | 接口已预留，可接入API |
| 📧 **Brevo邮件通知** | ✅ 完整 | HTML模板 + 一键直达 |
| 🎯 **全局策略引擎** | ✅ 完整 | 汇率联动消费建议 |
| 💾 **状态持久化** | ✅ 完整 | JSON存储 + 智能去重 |
| 🛡️ **反爬虫系统** | ✅ 完整 | 随机UA + 移动端Header + 延迟 |
| 🌐 **Streamlit Dashboard** | ✅ 完整 | 实时监控面板 |
| 🐳 **Docker支持** | ✅ 完整 | 一键部署 |
| ⚙️ **GitHub Actions** | ✅ 完整 | 云端定时任务 |

---

## 📂 文件结构说明

```
global-asset-monitor/
├── 📁 monitors/                      # 监控器模块（插件化架构）
│   ├── base_monitor.py              # ⭐ 抽象基类（所有监控器的父类）
│   ├── fx_monitor.py                # ⭐ 汇率监控（Z-Score + 4%门槛）
│   ├── jd_monitor.py                # ⭐ 京东自营监控（核心功能）
│   ├── amazon_monitor.py            # Amazon 监控
│   └── flight_monitor.py            # 机票监控（框架预留）
│
├── 📁 utils/                         # 工具模块
│   ├── anti_crawler.py              # ⭐ 反爬虫工具（UA池 + 随机延迟）
│   ├── notifier.py                  # ⭐ Brevo 邮件通知
│   ├── persistence.py               # ⭐ 状态持久化管理
│   └── global_strategy.py           # ⭐ 全局策略引擎（汇率联动）
│
├── 📁 .github/workflows/             # GitHub Actions
│   └── monitor.yml                  # 定时任务配置（每6小时）
│
├── ⚙️ config.yaml                    # ⭐ 核心配置文件
├── 🚀 main.py                        # ⭐ 主程序入口（定时任务）
├── 🌐 app.py                         # Streamlit Dashboard
├── 🧪 test.py                        # 单元测试
├── 🛠️ start.sh                       # 快速启动脚本
│
├── 🐳 Dockerfile                     # Docker 镜像
├── 🐳 docker-compose.yml             # Docker Compose
├── 📦 requirements.txt               # Python 依赖
│
├── 📖 README.md                      # 项目说明
├── 📘 USAGE_GUIDE.md                 # ⭐ 详细使用指南
├── 🔐 .env.example                   # 环境变量示例
├── 🗂️ last_check.json                # 状态文件（自动生成）
└── 📝 .gitignore                     # Git 忽略规则
```

**⭐ = 核心文件，建议优先查看**

---

## 🚀 快速开始（5分钟部署）

### 方式 1：本地运行（推荐新手）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 Brevo API Key

# 3. 编辑配置文件
nano config.yaml
# 填入要监控的京东 SKU、Amazon ASIN

# 4. 测试运行
python main.py --test-email  # 测试邮件
python main.py               # 运行一次完整检查
```

### 方式 2：使用快速启动脚本

```bash
chmod +x start.sh
./start.sh
# 选择对应的选项即可
```

### 方式 3：Docker 部署（推荐生产环境）

```bash
# 1. 编辑 .env
cp .env.example .env

# 2. 启动容器
docker-compose up -d

# 3. 访问 Dashboard
open http://localhost:8501
```

### 方式 4：GitHub Actions（无需服务器）

1. Fork/推送项目到 GitHub
2. 在 Settings → Secrets 中添加：
   - `BREVO_API_KEY`
   - `RECIPIENT_EMAIL`
3. Actions 将自动每6小时运行

---

## 🔧 核心配置说明

### 1. 汇率监控

```yaml
fx_monitor:
  enabled: true
  threshold_percent: 4.0     # ⭐ 关键：4%门槛
  zscore_window: 180         # ⭐ 180天Z-Score窗口
  pairs:
    usd_cny:
      base: USD
      quote: CNY
```

**工作原理：**
- 汇率变化 < 4% → 静默模式（跳过商品监控）
- 汇率变化 ≥ 4% → 触发全局策略 + 商品监控

### 2. 京东监控（核心功能）

```yaml
jd_monitor:
  enabled: true
  products:
    - sku_id: "100012345678"   # ⭐ 京东商品的 SKU ID
      name: "罗技 G304"
      expected_price: 199.0    # ⭐ 心理价位
```

**如何获取 SKU ID：**
```
https://item.jd.com/100012345678.html
                    ^^^^^^^^^^^^
                    这就是 SKU ID
```

**触发条件：**
- 价格 ≤ 心理价位 ✅
- 有货 ✅
- 是京东自营 ✅（非自营会警告）
- 有"百亿补贴" → Level 3 紧急通知

### 3. Amazon 监控

```yaml
amazon_monitor:
  enabled: true
  region: us
  products:
    - asin: "B08F3Y7QKW"      # Apple Gift Card
      expected_price: 100.0
```

---

## 📧 邮件通知效果

系统会发送 **HTML 格式**的精美邮件，包含：

```
┌─────────────────────────────────────────┐
│  🌍 全球资产监控系统                    │
│  您有新的价格提醒                       │
├─────────────────────────────────────────┤
│                                         │
│  ⚠️ USD/CNY 汇率人民币贬值 📉          │
│                                         │
│  当前汇率: 7.2345                       │
│  变化幅度: +4.23% (红色)               │
│  Z-Score: 2.15                          │
│                                         │
│  🎯 建议：暂缓海淘，增加京东巡检        │
│                                         │
│  [🔗 立即查看]  ← 一键直达按钮          │
├─────────────────────────────────────────┤
│                                         │
│  🛒 京东提醒 - 罗技 G304               │
│                                         │
│  当前价格: ¥199.00 (绿色)              │
│  心理价位: ¥220.00                      │
│  价差: ¥21.00                           │
│  库存状态: ✅ 有货                      │
│  商品属性: ✅ 京东自营                  │
│                                         │
│  触发原因：                             │
│  • 💰 价格达标                         │
│  • 📉 价格下降                         │
│                                         │
│  [🔗 立即查看]                          │
└─────────────────────────────────────────┘
```

---

## 🎯 实际使用场景

### 场景 1：抓住京东"百亿补贴"

```
08:00 - 系统检测到罗技 G304 出现"百亿补贴"标识
08:01 - 价格从 ¥249 降至 ¥199（低于心理价位 ¥220）
08:02 - 📧 发送 Level 3 紧急邮件通知
08:05 - 你点击"一键直达"按钮，成功下单
```

### 场景 2：人民币升值，海淘时机

```
周一 - USD/CNY 从 7.20 跌至 6.90（跌幅 4.2%）
周一 - 📧 汇率预警邮件：建议购买 Amazon Gift Card
周一 - 系统自动增加 Amazon 商品监控频率
周二 - Apple Gift Card 出现折扣（$95）
周二 - 📧 商品提醒邮件：节省 $5
```

### 场景 3：静默模式省资源

```
汇率变化仅 0.5%（未触发 4% 门槛）
→ 系统进入静默模式
→ 跳过京东和 Amazon 监控
→ 节省 API 调用和网络请求
→ 只有使用 --force 参数才会强制运行
```

---

## 🛡️ 反爬虫策略

系统内置多重反爬虫措施：

1. **移动端 User-Agent 池**（京东专用）
   - 随机选择 iOS/Android UA
   - 模拟真实移动设备

2. **PC端 User-Agent 池**（Amazon专用）
   - 随机选择 Chrome/Firefox/Safari

3. **随机延迟**
   - 请求间隔 1-3 秒
   - 模拟人类浏览行为

4. **移动端 Header 伪装**
   ```python
   headers = {
       'User-Agent': 'iPhone...',
       'Accept': 'text/html...',
       'Sec-Fetch-Dest': 'document',
       ...
   }
   ```

5. **请求重试机制**
   - 最多重试 3 次
   - 失败时增加延迟

---

## 📊 系统架构图

```
┌─────────────────────────────────────────────────────┐
│                   main.py (主程序)                   │
└─────────────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌───────────────┐ ┌───────────┐ ┌──────────────┐
│  FX Monitor   │ │ JD Monitor│ │Amazon Monitor│
│  (汇率监控)    │ │ (京东监控) │ │ (Amazon监控) │
└───────────────┘ └───────────┘ └──────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        ▼
        ┌───────────────────────────────┐
        │  Global Strategy (全局策略)    │
        │  - 汇率联动                   │
        │  - 消费建议                   │
        └───────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌─────────────┐ ┌──────────────┐ ┌────────────┐
│ Persistence │ │Anti-Crawler  │ │  Notifier  │
│ (持久化)    │ │ (反爬虫)      │ │  (通知)    │
└─────────────┘ └──────────────┘ └────────────┘
```

---

## 🔐 安全提醒

1. **永远不要将 `.env` 文件提交到 Git**
   - 已在 `.gitignore` 中配置

2. **使用环境变量存储敏感信息**
   ```bash
   export BREVO_API_KEY="your_key"
   export RECIPIENT_EMAIL="your_email"
   ```

3. **定期更新 User-Agent**
   - 编辑 `utils/anti_crawler.py`
   - 从 https://useragents.me/ 获取最新 UA

---

## 🆘 故障排查

### 问题：京东抓取失败（403）

**解决方案：**
```bash
# 1. 检查 User-Agent
cat utils/anti_crawler.py | grep "MOBILE_USER_AGENTS"

# 2. 增加延迟时间
# 编辑 jd_monitor.py，修改延迟参数
AntiCrawler.random_delay(2.5, 5.0)  # 原来是 1.5-3.5

# 3. 使用代理
export HTTP_PROXY=http://proxy.com:8080
```

### 问题：邮件发送失败

**解决方案：**
```bash
# 1. 测试邮件配置
python main.py --test-email

# 2. 检查 API Key
echo $BREVO_API_KEY

# 3. 查看 Brevo 控制台
# https://app.brevo.com/logs/transactional
```

### 问题：GitHub Actions 运行失败

**解决方案：**
1. 检查 Secrets 是否配置
2. 查看 Actions 日志
3. 确认 requirements.txt 依赖完整

---

## 📈 后续扩展建议

### 1. 添加 Telegram 通知

```python
# utils/telegram_notifier.py
import requests

def send_telegram(message):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    requests.post(url, data={'chat_id': chat_id, 'text': message})
```

### 2. 接入机票 API

推荐使用：
- **Skyscanner API**
- **Kiwi.com API**
- **Google Flights**（需抓取）

### 3. 数据库支持

将 `last_check.json` 升级为 SQLite/PostgreSQL：

```python
# utils/db_persistence.py
import sqlite3

class DatabasePersistence:
    def __init__(self, db_path='monitor.db'):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS prices (
                key TEXT PRIMARY KEY,
                value REAL,
                timestamp TEXT,
                metadata TEXT
            )
        ''')
```

### 4. 可视化图表

在 Streamlit Dashboard 中添加价格趋势图：

```python
import plotly.express as px

# 读取历史数据
df = load_historical_data()

# 绘制折线图
fig = px.line(df, x='timestamp', y='price', title='价格趋势')
st.plotly_chart(fig)
```

---

## 📞 技术支持

- **GitHub Issues**: 提交 Bug
- **Pull Requests**: 贡献代码
- **文档**: 查看 `USAGE_GUIDE.md`

---

## 📜 许可证

MIT License - 可自由使用、修改、分发

---

## 🎉 结语

这是一个**生产级、可扩展**的监控系统，包含：

✅ **完整的代码实现**（2000+ 行）
✅ **详细的文档**（README + USAGE_GUIDE）
✅ **多种部署方式**（本地/Docker/GitHub Actions/HF Spaces）
✅ **反爬虫加固**（UA池 + 随机延迟 + 移动端Header）
✅ **智能策略**（汇率联动 + 静默模式）

**祝你使用愉快！如有任何问题，欢迎反馈。**

---

**项目作者**: Claude 4.5 Sonnet  
**创建日期**: 2026-02-16  
**版本**: v1.0
