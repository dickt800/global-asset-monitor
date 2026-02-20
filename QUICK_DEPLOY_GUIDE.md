# 🚀 5分钟快速部署指南

## 📦 你已经下载了什么

**文件：** `global-asset-monitor.tar.gz`

**内容：** 完整的监控系统，包含所有功能：
- ✅ 中国版汇率监控（银行挂牌价）
- ✅ Amazon 礼品卡监控
- ✅ 京东自营监控
- ✅ 多收件人通知
- ✅ Web GUI
- ✅ 所有文档

---

## 🚀 快速部署（3步）

### 步骤 1：解压文件

**Windows：**
```cmd
# 双击 global-asset-monitor.tar.gz
# Windows 会自动解压（或者用 7-Zip）
```

**Mac/Linux：**
```bash
tar -xzf global-asset-monitor.tar.gz
cd global-asset-monitor
```

---

### 步骤 2：安装依赖

```bash
pip install -r requirements.txt --break-system-packages
```

**如果提示错误：**
```bash
# Python 3.11+ 需要加这个参数
pip install -r requirements.txt --break-system-packages

# 或者创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

---

### 步骤 3：配置系统

#### A. 配置收件人（必须）

编辑 `recipients.json`：

```bash
nano recipients.json  # Mac/Linux
notepad recipients.json  # Windows
```

**修改为你的真实信息：**

```json
{
  "recipients": [
    {
      "name": "你的真实名字",
      "email": "你的真实邮箱@gmail.com",
      "enabled": true,
      "role": "owner",
      "preferences": {
        "notify_fx": true,
        "notify_jd": true,
        "notify_amazon": true,
        "notify_gift_card": true
      },
      "notes": "系统主人"
    }
  ]
}
```

**如果要添加朋友：**

```json
{
  "recipients": [
    {
      "name": "你的名字",
      "email": "你的邮箱@gmail.com",
      "enabled": true,
      "role": "owner",
      "preferences": {...}
    },
    {
      "name": "朋友的名字",
      "email": "朋友的邮箱@qq.com",
      "enabled": true,
      "role": "subscriber",
      "preferences": {
        "notify_fx": false,
        "notify_jd": false,
        "notify_amazon": false,
        "notify_gift_card": true
      },
      "notes": "只要礼品卡通知"
    }
  ]
}
```

#### B. 配置邮件发送（必须）

**方法 1：创建 .env 文件（推荐）**

创建文件 `.env`：

```bash
# Brevo API 配置
BREVO_API_KEY=你的Brevo_API_Key

# 发件人信息（可选，有默认值）
SENDER_EMAIL=noreply@monitor.com
SENDER_NAME=全球资产监控系统
```

**获取 Brevo API Key：**
1. 注册 https://www.brevo.com （免费）
2. 进入 Settings → API Keys
3. 创建新的 API Key
4. 复制粘贴到 .env 文件

**方法 2：设置环境变量**

**Mac/Linux：**
```bash
export BREVO_API_KEY="你的API_Key"
```

**Windows：**
```cmd
set BREVO_API_KEY=你的API_Key
```

#### C. 配置监控商品（可选）

编辑 `config.yaml`：

```bash
nano config.yaml
```

**添加你想监控的商品：**

```yaml
# 汇率监控
fx_monitor_cn:
  enabled: true
  threshold_percent: 4.0
  banks:
    - boc  # 中国银行

# Amazon 礼品卡监控
amazon_monitor:
  enabled: true
  monitor_gift_cards: true
  monitor_reload: true
  products:
    - asin: "B08F3Y7QKW"
      name: "Apple Gift Card $100"
      expected_price: 100.0
      is_gift_card: true
      priority: high

# 京东监控（可选）
jd_monitor:
  enabled: true
  products:
    - sku_id: "100012345678"
      name: "罗技 G304 鼠标"
      expected_price: 199.0
      priority: high
```

---

### 步骤 4：运行测试

```bash
python main.py
```

**你应该看到：**

```
💱 汇率监控
================================================
✅ 加载了 1 个收件人
📍 使用中国版监控器（监控银行挂牌价）
  中国银行: 7.1450
🏆 最优惠: 中国银行 7.1450
✅ 汇率正常，无需提醒

🛍️  Amazon 监控
================================================
✅ 加载了 1 个收件人
🎁 检查 Amazon Reload 促销...
  未检测到 Reload 促销
🔍 检查 Amazon 商品: Apple Gift Card $100
  价格: $100.00 | 库存: In Stock
✅ Amazon 商品暂无变化

🛒 京东监控
================================================
⚠️  静默模式：汇率变化未达到4%门槛，跳过商品监控

✅ 监控完成
```

---

## 🎨 启动 Web GUI（可选）

```bash
streamlit run app.py
```

浏览器会自动打开：`http://localhost:8501`

**你可以在 GUI 里：**
- ✅ 可视化添加商品
- ✅ 查看监控历史
- ✅ 查看促销日历
- ✅ 管理收件人
- ✅ 查看推荐网站

---

## ⚙️ 定时运行（推荐）

### 方法 1：GitHub Actions（推荐）⭐

**优势：**
- ✅ 免费
- ✅ 自动运行
- ✅ 不需要自己的服务器

**步骤：**

1. 在 GitHub 创建仓库
2. 上传整个文件夹
3. 在 Settings → Secrets 添加：
   - `BREVO_API_KEY`
4. GitHub Actions 会自动每6小时运行一次

**已经配置好了：** `.github/workflows/monitor.yml`

---

### 方法 2：本地定时任务

**Mac/Linux (crontab)：**

```bash
# 编辑定时任务
crontab -e

# 添加这一行（每6小时运行一次）
0 */6 * * * cd /path/to/global-asset-monitor && python main.py
```

**Windows (任务计划程序)：**

1. 打开"任务计划程序"
2. 创建基本任务
3. 触发器：每6小时
4. 操作：启动程序
   - 程序：`python`
   - 参数：`main.py`
   - 起始于：`C:\path\to\global-asset-monitor`

---

### 方法 3：Docker（高级）

```bash
# 构建镜像
docker-compose build

# 运行
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 📂 文件结构说明

```
global-asset-monitor/
├── main.py                    # 主程序（CLI）
├── app.py                     # Web GUI
├── config.yaml                # 系统配置
├── recipients.json            # 收件人列表 ⭐ 必须配置
├── requirements.txt           # Python 依赖
├── .env.example               # 环境变量模板
├── .gitignore                 # Git 忽略文件
│
├── monitors/                  # 监控器模块
│   ├── __init__.py
│   ├── base_monitor.py
│   ├── fx_monitor.py          # 国际版汇率
│   ├── fx_monitor_cn.py       # 中国版汇率 ⭐ 推荐
│   ├── jd_monitor.py          # 京东监控
│   ├── amazon_monitor.py      # Amazon 监控
│   └── flight_monitor.py      # 机票监控（框架）
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── notifier.py            # Brevo 邮件通知 ⭐ 已升级多收件人
│   ├── persistence.py         # 状态持久化
│   ├── anti_crawler.py        # 反爬虫
│   └── global_strategy.py     # 全局策略
│
├── docs/                      # 文档
│   ├── README.md              # 项目说明
│   ├── USAGE_GUIDE.md         # 使用指南
│   ├── FX_MONITOR_GUIDE_CN.md # 汇率监控说明
│   ├── GIFT_CARD_MONITOR_GUIDE.md  # 礼品卡监控
│   ├── MULTI_RECIPIENTS_GUIDE.md   # 多收件人指南 ⭐ 新增
│   ├── DUAL_LABEL_CARD_GUIDE.md    # 双标卡说明
│   ├── ZERO_LIMIT_CARD_GUIDE.md    # 0额度卡指南
│   └── COMPLETE_GIFT_CARD_GUIDE.md # 礼品卡完全指南
│
├── .github/                   # GitHub Actions
│   └── workflows/
│       └── monitor.yml        # 定时运行配置
│
├── Dockerfile                 # Docker 配置
├── docker-compose.yml         # Docker Compose
└── start.sh                   # 快速启动脚本
```

---

## 🎯 核心配置文件

### 1. recipients.json ⭐ 必须配置

**作用：** 配置谁接收通知

**位置：** 项目根目录

**示例：**
```json
{
  "recipients": [
    {
      "name": "你的名字",
      "email": "你的邮箱",
      "enabled": true,
      "role": "owner",
      "preferences": {
        "notify_fx": true,
        "notify_jd": true,
        "notify_amazon": true,
        "notify_gift_card": true
      }
    }
  ]
}
```

---

### 2. config.yaml

**作用：** 配置监控商品和参数

**位置：** 项目根目录

**核心配置：**
```yaml
# 汇率监控（中国版）
fx_monitor_cn:
  enabled: true
  threshold_percent: 4.0
  banks:
    - boc

# Amazon 监控
amazon_monitor:
  enabled: true
  monitor_gift_cards: true
  monitor_reload: true
  products:
    - asin: "B08F3Y7QKW"
      name: "Apple Gift Card $100"
      expected_price: 100.0
      is_gift_card: true
```

---

### 3. .env

**作用：** 配置 API Key 等敏感信息

**位置：** 项目根目录

**内容：**
```
BREVO_API_KEY=你的Brevo_API_Key
```

---

## 🔧 常用命令

### 运行监控

```bash
python main.py              # 正常运行
python main.py --force      # 强制运行（忽略静默模式）
python main.py --test-email # 测试邮件发送
```

### 启动 Web GUI

```bash
streamlit run app.py
```

### 查看日志

```bash
# 如果使用 GitHub Actions
# 在 GitHub 仓库 → Actions → 点击运行记录

# 如果使用 Docker
docker-compose logs -f

# 如果本地运行
# 直接看终端输出
```

---

## 📧 测试邮件发送

**确保配置正确：**

```bash
python main.py --test-email
```

**你应该收到测试邮件：**

```
标题：📬 全球资产监控提醒 - 1 条新消息
内容：
  你好，你的名字！
  系统主人
  
  🧪 测试通知
  这是一封测试邮件，用于验证 Brevo 配置和收件人列表是否正确。
  
  [🔗 立即查看]
```

---

## ⚠️ 常见问题

### Q1: 没有收到邮件

**检查：**
1. `recipients.json` 中邮箱是否正确
2. `recipients.json` 中 `enabled` 是否为 `true`
3. `.env` 文件中 `BREVO_API_KEY` 是否正确
4. 垃圾邮件文件夹

### Q2: 运行报错

**常见错误：**

```
ModuleNotFoundError: No module named 'requests'
```

**解决：**
```bash
pip install -r requirements.txt --break-system-packages
```

### Q3: JSON 格式错误

**错误示例：**
```json
{
  "recipients": [
    {...},
    {...},  ← 最后一个对象后面不能有逗号
  ]
}
```

**正确格式：**
```json
{
  "recipients": [
    {...},
    {...}
  ]
}
```

**验证 JSON 格式：**
```bash
python -m json.tool recipients.json
```

---

## 🎉 部署完成！

### 你现在应该：

✅ 下载了 `global-asset-monitor.tar.gz`
✅ 解压到本地
✅ 配置了 `recipients.json`
✅ 配置了 `.env`（Brevo API Key）
✅ 安装了依赖
✅ 运行测试成功
✅ 收到了测试邮件

### 接下来：

1. **春节回家后部署**
2. **汇率便宜时给两张卡购汇**
3. **等黑五买礼品卡**
4. **给朋友代购**

---

## 📚 文档索引

| 文档 | 说明 |
|-----|------|
| **MULTI_RECIPIENTS_GUIDE.md** | 多收件人使用指南 ⭐ |
| **FX_MONITOR_GUIDE_CN.md** | 中国版汇率监控说明 |
| **GIFT_CARD_MONITOR_GUIDE.md** | 礼品卡监控说明 |
| **DUAL_LABEL_CARD_GUIDE.md** | 双标卡问题解析 |
| **ZERO_LIMIT_CARD_GUIDE.md** | 0额度卡使用指南 |
| **COMPLETE_GIFT_CARD_GUIDE.md** | 礼品卡购买完全指南 |

**所有文档都在项目根目录！**

---

## 🆘 需要帮助？

**如果遇到问题：**

1. 查看对应的文档（如上表）
2. 检查配置文件格式
3. 运行测试邮件：`python main.py --test-email`
4. 查看终端输出的错误信息

---

**祝你部署顺利！春节快乐！** 🎉🧧

---

**文档版本**: v1.0  
**创建日期**: 2026-02-16  
**系统版本**: v2.0 完整版
