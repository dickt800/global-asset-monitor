# 📘 全球资产监控系统 - 使用指南

## 目录

1. [快速开始](#快速开始)
2. [配置详解](#配置详解)
3. [监控器使用](#监控器使用)
4. [部署方式](#部署方式)
5. [常见问题](#常见问题)
6. [高级用法](#高级用法)

---

## 快速开始

### 前置要求

- Python 3.9+
- pip
- （可选）Docker

### 步骤 1：克隆/下载项目

```bash
git clone <your-repo-url>
cd global-asset-monitor
```

### 步骤 2：安装依赖

**方式 A：使用快速启动脚本（推荐）**

```bash
chmod +x start.sh
./start.sh
```

**方式 B：手动安装**

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 步骤 3：配置环境变量

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置
nano .env  # 或使用你喜欢的编辑器
```

填入以下信息：

```env
BREVO_API_KEY=xkeysib-xxxxxxxxxxxx
RECIPIENT_EMAIL=your_email@gmail.com
```

**获取 Brevo API Key：**

1. 访问 https://www.brevo.com/
2. 注册免费账户（每天 300 封邮件额度）
3. 进入 Settings → API Keys
4. 生成新的 API Key

### 步骤 4：配置监控项

编辑 `config.yaml`：

```yaml
# 示例：监控京东鼠标
jd_monitor:
  enabled: true
  products:
    - sku_id: "100012345678"  # 替换为真实 SKU
      name: "罗技 G304"
      expected_price: 199.0
```

**如何获取京东 SKU ID？**

1. 打开京东商品页面
2. URL 中的数字即为 SKU ID
   ```
   https://item.jd.com/100012345678.html
                    ^^^^^^^^^^^^
                    这就是 SKU ID
   ```

### 步骤 5：运行测试

```bash
# 测试邮件配置
python main.py --test-email

# 运行一次完整检查
python main.py

# 强制运行（忽略静默模式）
python main.py --force
```

---

## 配置详解

### 汇率监控配置

```yaml
fx_monitor:
  enabled: true              # 是否启用
  threshold_percent: 4.0     # 触发门槛（%）
  zscore_window: 180         # Z-Score 窗口（天）
  pairs:
    usd_cny:                 # 货币对名称（自定义）
      base: USD              # 基础货币
      quote: CNY             # 目标货币
```

**支持的货币代码：**
- USD, EUR, GBP, JPY, CNY, HKD, AUD, CAD 等

### 京东监控配置

```yaml
jd_monitor:
  enabled: true
  products:
    - sku_id: "100012345678"     # 商品 SKU ID（必填）
      name: "商品名称"            # 显示名称（必填）
      expected_price: 199.0      # 心理价位（必填）
      priority: high             # 优先级（可选）
```

**优先级说明：**
- `high`: 高优先级（实时监控）
- `medium`: 中优先级
- `low`: 低优先级

### Amazon 监控配置

```yaml
amazon_monitor:
  enabled: true
  region: us                     # 区域：us/uk/de/jp
  products:
    - asin: "B08F3Y7QKW"        # Amazon ASIN（方式1）
      name: "Apple Gift Card"
      expected_price: 100.0
    
    - url: "https://..."         # 完整 URL（方式2）
      name: "商品名称"
      expected_price: 50.0
```

**如何获取 ASIN？**

1. 打开 Amazon 商品页面
2. 查看 URL 或页面的 "Product details"
   ```
   https://www.amazon.com/dp/B08F3Y7QKW
                            ^^^^^^^^^^^
                            这就是 ASIN
   ```

---

## 监控器使用

### 汇率监控器

**工作原理：**

1. 每次运行时获取当前汇率
2. 与上次记录对比，计算变化百分比
3. 计算 180 天 Z-Score（统计学异常检测）
4. 如果变化 ≥ 4%，触发通知

**静默模式：**

- 当汇率变化 < 4% 时，系统进入静默模式
- 静默模式下跳过商品监控（节省资源）
- 使用 `--force` 参数可忽略静默模式

**示例输出：**

```
💱 汇率监控
================================================
USD/CNY 当前: 7.1234 | 变化: -4.23% | Z-Score: -2.15
✅ 检测到 1 条汇率预警
```

### 京东监控器

**工作原理：**

1. 使用移动端 User-Agent 访问 H5 页面
2. 解析价格、库存、自营状态
3. 检测"百亿补贴"、"秒杀"等活动
4. 与心理价位对比

**触发条件：**

- 价格 ≤ 心理价位 ✅
- 有货 ✅
- 价格低于上次提醒价格 ✅

**通知级别：**

- Level 3：百亿补贴/秒杀
- Level 2：价格达标
- Level 1：价格下降

**示例输出：**

```
🛒 京东自营监控
================================================
🔍 检查京东商品: 罗技 G304 (SKU: 100012345678)
  价格: ¥199.00 | 库存: 有货 | 自营: 是 | 补贴: 否
✅ 检测到 1 条商品提醒
```

### Amazon 监控器

**工作原理：**

1. 使用 PC 端 User-Agent
2. 解析价格和库存信息
3. 与目标价格对比

**触发条件：**

- 价格 ≤ 目标价格 ✅
- 有货 ✅

---

## 部署方式

### 1. 本地定时任务（推荐）

**Linux/macOS (Cron):**

```bash
# 编辑 crontab
crontab -e

# 每6小时运行一次
0 */6 * * * cd /path/to/global-asset-monitor && /path/to/venv/bin/python main.py
```

**Windows (Task Scheduler):**

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每天多次
4. 操作：启动程序
   - 程序：`C:\path\to\python.exe`
   - 参数：`main.py`
   - 起始于：项目目录

### 2. GitHub Actions（云端）

参考 `.github/workflows/monitor.yml`

**优点：**
- 无需自己的服务器
- 免费（每月 2000 分钟）
- 自动运行

**设置步骤：**

1. Fork/推送项目到 GitHub
2. 进入 Settings → Secrets
3. 添加以下 Secrets：
   - `BREVO_API_KEY`
   - `RECIPIENT_EMAIL`
4. Actions 将自动每6小时运行

### 3. Docker 部署

**启动容器：**

```bash
docker-compose up -d
```

或手动运行：

```bash
docker build -t monitor .
docker run -d \
  -e BREVO_API_KEY=xxx \
  -e RECIPIENT_EMAIL=xxx \
  monitor
```

### 4. Hugging Face Spaces

**步骤：**

1. 创建 Streamlit Space
2. 上传项目文件
3. 在 Settings 中添加环境变量
4. 自动部署

**注意：** HF Spaces 主要用于展示 Dashboard，定时任务需配合 GitHub Actions

---

## 常见问题

### Q1: 京东抓取失败（403 错误）

**原因：** 反爬虫检测

**解决方案：**

1. 检查 `utils/anti_crawler.py` 中的 User-Agent 是否过时
2. 增加随机延迟时间
3. 使用代理（配置 `HTTP_PROXY` 环境变量）

```bash
export HTTP_PROXY=http://proxy.com:8080
```

### Q2: 邮件发送失败

**可能原因：**

1. API Key 错误
2. 邮件额度用完
3. 收件人邮箱无效

**调试步骤：**

```bash
# 发送测试邮件
python main.py --test-email

# 检查 Brevo 控制台
# https://app.brevo.com/logs/transactional
```

### Q3: 汇率数据获取失败

**原因：** API 限流或网络问题

**解决方案：**

1. 更换汇率 API（编辑 `monitors/fx_monitor.py`）
2. 检查网络连接
3. 查看 API 使用限制

**备选 API：**
- Alpha Vantage
- ExchangeRate-API
- Open Exchange Rates

### Q4: 静默模式不生效

**检查：**

```bash
# 查看当前汇率变化
python main.py  # 会显示变化百分比

# 强制运行
python main.py --force
```

---

## 高级用法

### 1. 自定义通知模板

编辑 `utils/notifier.py` 中的 `_build_html()` 方法：

```python
html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        /* 自定义样式 */
    </style>
</head>
<body>
    <!-- 自定义内容 -->
</body>
</html>
"""
```

### 2. 添加新的监控器

1. 创建新文件 `monitors/custom_monitor.py`
2. 继承 `BaseMonitor`
3. 实现 `check()` 方法

示例：

```python
from monitors.base_monitor import BaseMonitor

class CustomMonitor(BaseMonitor):
    def check(self):
        # 你的监控逻辑
        return [{
            'title': '自定义通知',
            'message': '...',
            'url': '...',
            'price_info': '...',
            'level': 2
        }]
    
    def _should_notify(self, current_value, last_value):
        return current_value < last_value
```

3. 在 `main.py` 中注册

### 3. 集成其他通知渠道

**Telegram Bot：**

```python
import requests

def send_telegram(message):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = {'chat_id': chat_id, 'text': message}
    
    requests.post(url, data=data)
```

**企业微信：**

```python
def send_wechat(message):
    webhook = os.getenv('WECHAT_WEBHOOK')
    data = {
        "msgtype": "text",
        "text": {"content": message}
    }
    requests.post(webhook, json=data)
```

### 4. 数据分析

利用 `last_check.json` 进行趋势分析：

```python
import json
import pandas as pd

# 读取历史数据
with open('last_check.json', 'r') as f:
    data = json.load(f)

# 转换为 DataFrame
df = pd.DataFrame.from_dict(data, orient='index')

# 分析
print(df.describe())
```

---

## 支持与反馈

- **GitHub Issues**: 提交 Bug 或功能请求
- **Pull Requests**: 欢迎贡献代码

---

**祝你使用愉快！🎉**
