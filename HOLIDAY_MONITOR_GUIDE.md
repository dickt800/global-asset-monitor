# 🗓️ 节日监控混合方案配置指南

## 🎯 混合方案说明

### 什么是混合方案？

```
自动检索（Google API）+ 固定日期（保底）
    ↓
优先使用：检索到的日期（最准确）
备用方案：固定日期/算法（保底）
    ↓
万无一失！
```

---

## 🚀 快速配置（3步）

### 步骤 1：获取 Google Custom Search API Key

#### 1.1 创建项目

1. 访问：https://console.cloud.google.com/
2. 登录你的 Google 账号
3. 点击"选择项目" → "新建项目"
4. 项目名称：`Holiday Monitor`
5. 点击"创建"

#### 1.2 启用 API

1. 在项目中，点击"启用 API 和服务"
2. 搜索：`Custom Search API`
3. 点击"启用"

#### 1.3 创建凭据

1. 点击"创建凭据"
2. 选择"API 密钥"
3. 复制 API 密钥（类似：`AIzaSyC...`）
4. 保存备用

#### 1.4 配额说明

**免费额度：**
- 每天 100 次搜索请求
- 完全够用（我们每周只搜 1-2 次）

**收费标准：**
- 超过 100 次/天：$5/1000 次
- 但你不会超（放心）

---

### 步骤 2：创建自定义搜索引擎

#### 2.1 访问控制台

1. 访问：https://cse.google.com/cse/
2. 登录你的 Google 账号
3. 点击"添加"

#### 2.2 配置搜索引擎

1. **搜索的网站：** `www.google.com`（搜索整个网络）
2. **语言：** 英语
3. **搜索引擎名称：** `Holiday Search`
4. 点击"创建"

#### 2.3 获取搜索引擎 ID

1. 创建后，点击"控制面板"
2. 找到"搜索引擎 ID"（类似：`017576662512468239146:omuauf_lfve`）
3. 复制保存

#### 2.4 启用公共搜索

1. 在"基本信息"中
2. 找到"搜索整个网络"
3. 打开此选项
4. 保存

---

### 步骤 3：配置环境变量

编辑 `.env` 文件：

```env
# Brevo 邮件（已有）
BREVO_API_KEY=你的Brevo_API_Key

# Google Custom Search API（新增）
GOOGLE_SEARCH_API_KEY=AIzaSyC...（步骤1.3的密钥）
GOOGLE_SEARCH_CX=017576662512468239146:omuauf_lfve（步骤2.3的ID）
```

保存文件。

---

### 步骤 4：启用节日监控

编辑 `config.yaml`：

```yaml
# 节日监控（新增）
holiday_monitor:
  enabled: true
  
  # 启用的节日
  holidays:
    - prime_day       # Prime Day（需要检索）
    - black_friday    # 黑色星期五（算法+检索验证）
    - cyber_monday    # 网络星期一（算法+检索验证）
    - christmas       # 圣诞节（固定日期）
    - independence_day  # 独立日（固定日期）
```

---

## 📋 工作流程详解

### Prime Day（需要检索）⭐

**6月15日 - 7月10日：自动检索阶段**

```
6月15日：
系统：开始每周检索 "Prime Day 2026 date"
    ↓
6月22日：
系统：继续检索
    ↓
6月29日：
系统：继续检索
    ↓
7月6日：
系统：检索到 "July 15, 2026"
  ✅ 记录日期
  ✅ 停止检索
```

**7月13日（提前2天）：自动提醒**

```
系统发邮件：
标题：📢 Prime Day 即将到来（7月15日）

内容：
"Prime Day 日期已确定：7月15日
 距离：2天
 
 从明天开始，每天查价：
 • Amazon.com
 • 搜索 Apple Gift Card
 
 [🔗 Amazon 礼品卡页面]"
```

**如果检索失败（保底方案）：**

```
7月10日还没检索到：
    ↓
系统发邮件：
标题：⚠️ Prime Day 日期未公布，请手动查看

内容：
"系统未能检索到 Prime Day 日期。
 
 请手动查看 Amazon 公告：
 [🔗 点击自动搜索 Prime Day 2026]
 
 找到日期后：
 1. 编辑 holidays.yaml
 2. 填写：prime_day.date = '2026-07-15'
 3. 保存
 
 系统会在日期前2天自动提醒你"
```

---

### Black Friday（算法 + 检索验证）⭐

**固定算法：**
```
11月第四个周五
    ↓
2026年：11月27日（系统自动计算）
```

**10月1日：检索验证**

```
系统检索："Black Friday 2026 date"
    ↓
【情况1】检索到：November 27, 2026
  → 和算法一致 ✅
  → 使用这个日期
    ↓
【情况2】检索到：November 28, 2026（不一致）
  → ⚠️ 警告！
  → 发邮件：
    "检索到的日期(11月28日)和算法(11月27日)不一致！
     请手动确认：[搜索链接]"
    ↓
【情况3】检索失败
  → 使用算法日期（保底）
  → 11月20日（提前一周）提醒你
```

**11月20日（提前一周）：自动提醒**

```
系统发邮件：
标题：🔥 黑色星期五即将到来（11月27日）

内容：
"黑色星期五：11月27日
 距离：7天
 
 从今天开始，每天查价：
 • Amazon.com
 • Newegg.com
 • 搜索 Apple Gift Card
 
 持续到 Cyber Monday（11月30日）
 
 [🔗 Amazon] [🔗 Newegg]"
```

---

### Christmas（固定日期，不检索）

```
12月25日（写死）
    ↓
12月18日（提前一周）
    ↓
系统发邮件：
"圣诞节即将到来，12月每周末查价"
    ↓
不需要检索 ✅
```

---

## 📊 检索频率

| 节日 | 检索开始 | 检索频率 | 检索查询 | 保底方案 |
|-----|---------|---------|---------|---------|
| **Prime Day** | 6月15日 | 每周1次 | "Prime Day 2026 date" | 7月10日发邮件提醒手动查 |
| **Black Friday** | 10月1日 | 一次 | "Black Friday 2026 date" | 用算法（11月第四个周五） |
| **Cyber Monday** | 10月1日 | 一次 | "Cyber Monday 2026 date" | 用算法（黑五+3天） |
| Christmas | - | 不检索 | - | 固定12月25日 |
| Independence Day | - | 不检索 | - | 固定7月4日 |

**月度总计：**
- 6月：4次（Prime Day 每周）
- 7月：2次（Prime Day 每周，直到找到）
- 10月：2次（黑五 + Cyber Monday 各1次）
- 其他月份：0次

**全年总计：约 8-10 次**（远低于每天100次的免费额度）

---

## ⚙️ 配置选项

### config.yaml 详细配置

```yaml
holiday_monitor:
  enabled: true
  
  # 检索设置
  search:
    # 是否启用自动检索
    enabled: true
    
    # 检索失败后重试次数
    max_retries: 3
    
    # 检索间隔（天）
    retry_interval: 7
  
  # 启用的节日
  holidays:
    - prime_day
    - black_friday
    - cyber_monday
    - christmas
    - independence_day
    - labor_day
    - back_to_school
```

### holidays.yaml 详细配置

```yaml
prime_day:
  enabled: true
  
  # 检索配置
  search:
    enabled: true  # 是否启用自动检索
    query: "Prime Day 2026 date when"
    start_date: "2026-06-15"  # 开始检索日期
    frequency: "weekly"  # 检索频率：daily/weekly
    fallback_date: "2026-07-10"  # 检索失败截止日期
  
  # 如果检索到日期，会自动更新这里
  date: ""  # 留空表示未确定
  
  # 提前提醒
  advance_days: 2
```

---

## 🔍 测试配置

### 测试 Google Search API

```bash
# 测试搜索
python -c "
import os
import requests

api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
cx = os.getenv('GOOGLE_SEARCH_CX')

url = 'https://www.googleapis.com/customsearch/v1'
params = {
    'key': api_key,
    'cx': cx,
    'q': 'Prime Day 2026 date',
    'num': 3
}

response = requests.get(url, params=params)
print(f'状态码: {response.status_code}')
print(f'配额剩余: {response.headers.get(\"X-RateLimit-Remaining\")}')

if response.status_code == 200:
    data = response.json()
    print(f'找到 {len(data.get(\"items\", []))} 个结果')
    for item in data.get('items', [])[:3]:
        print(f'- {item[\"title\"]}')
        print(f'  {item[\"snippet\"]}')
"
```

**期望输出：**
```
状态码: 200
配额剩余: 99
找到 3 个结果
- Amazon Prime Day 2026: Date, Deals, and What to Expect
  Prime Day 2026 is expected to take place in mid-July...
```

---

## ⚠️ 常见问题

### Q1: API 配额不够怎么办？

**A:** 不会的，原因：
- 免费额度：100次/天
- 实际使用：1-2次/周
- 全年总计：8-10次

### Q2: 检索不到日期怎么办？

**A:** 系统会：
1. 自动重试（每周检索）
2. 检索失败截止日期：发邮件提醒你手动查
3. 使用保底方案（固定日期/算法）

### Q3: 检索到错误日期怎么办？

**A:** 对于重要节日（黑五），系统会：
1. 和算法对比
2. 不一致 → 发邮件警告你
3. 你手动确认

### Q4: 不想用 Google API 怎么办？

**A:** 可以关闭自动检索：

```yaml
holiday_monitor:
  search:
    enabled: false  # 关闭自动检索
```

系统会只用：
- 固定日期（圣诞节、独立日）
- 固定算法（黑五、Cyber Monday）
- 手动填写（Prime Day）

---

## 🎉 总结

### 混合方案的优势

✅ **万无一失**
- 优先：自动检索（最准确）
- 保底：固定日期/算法

✅ **省心**
- 自动检索
- 自动验证
- 自动提醒

✅ **免费**
- Google API：100次/天免费
- 实际使用：1-2次/周
- 完全够用

✅ **可靠**
- 检索失败 → 保底方案
- 日期冲突 → 警告通知
- 不会错过

---

## 📞 获取帮助

### Google API 配置问题

- 官方文档：https://developers.google.com/custom-search/v1/introduction
- 控制台：https://console.cloud.google.com/

### 系统配置问题

- 查看日志：运行系统时的终端输出
- 检查配置：`config.yaml` 和 `.env` 文件

---

**配置完成后，运行 `python main.py` 测试！**

---

**文档版本**: v1.0  
**创建日期**: 2026-02-16  
**方案类型**: 混合方案（自动检索 + 固定日期）
