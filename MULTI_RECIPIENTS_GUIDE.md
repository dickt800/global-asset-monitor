# 📧 多收件人通知指南

## 🎯 使用场景

### 你和朋友的对话

```
朋友："我也得备一点礼品卡用了。有时候对苹果充值用"
你："我有优惠，立刻也会通知你"
你："这样吧，我在这个系统里面加你的邮箱"
```

**现在你可以轻松实现了！** ✅

---

## 🚀 快速开始

### 步骤 1：编辑 recipients.json

```bash
nano recipients.json
```

### 步骤 2：添加收件人

```json
{
  "recipients": [
    {
      "name": "你的名字",
      "email": "your_email@example.com",
      "enabled": true,
      "role": "owner",
      "preferences": {
        "notify_fx": true,
        "notify_jd": true,
        "notify_amazon": true,
        "notify_gift_card": true
      },
      "notes": "系统主人，接收所有通知"
    },
    {
      "name": "朋友A",
      "email": "friend_a@example.com",
      "enabled": true,
      "role": "subscriber",
      "preferences": {
        "notify_fx": false,
        "notify_jd": false,
        "notify_amazon": false,
        "notify_gift_card": true
      },
      "notes": "只要苹果礼品卡优惠通知"
    }
  ]
}
```

### 步骤 3：运行系统

```bash
python main.py
```

**系统会自动：**
- 读取所有 `enabled: true` 的收件人
- 根据每个人的 `preferences` 筛选通知
- 给符合条件的人发邮件
- 邮件中显示个性化称呼

---

## 📖 字段说明

### 必填字段

| 字段 | 类型 | 说明 | 示例 |
|-----|------|------|------|
| **name** | string | 收件人名字 | "张三" |
| **email** | string | 邮箱地址 | "zhangsan@gmail.com" |
| **enabled** | boolean | 是否启用 | true / false |

### 可选字段

| 字段 | 类型 | 说明 | 默认值 |
|-----|------|------|--------|
| **role** | string | 角色标识 | "subscriber" |
| **preferences** | object | 通知偏好 | 全部 true |
| **notes** | string | 备注信息 | "" |

### role（角色）

| 值 | 说明 | 邮件中显示 |
|----|------|-----------|
| **owner** | 系统主人 | "系统主人" |
| **subscriber** | 订阅者 | 不显示 |

### preferences（通知偏好）

| 字段 | 说明 | 对应通知类型 |
|-----|------|-------------|
| **notify_fx** | 汇率通知 | USD/CNY 汇率变化 |
| **notify_jd** | 京东通知 | 京东商品降价 |
| **notify_amazon** | Amazon 通知 | Amazon 商品降价 |
| **notify_gift_card** | 礼品卡通知 | Apple/Amazon 礼品卡打折 |

---

## 💡 常见配置示例

### 示例 1：朋友只要礼品卡通知

**需求：**
- 朋友只想知道 Apple 礼品卡什么时候打折
- 不关心汇率、京东、普通商品

**配置：**
```json
{
  "name": "朋友小明",
  "email": "xiaoming@qq.com",
  "enabled": true,
  "role": "subscriber",
  "preferences": {
    "notify_fx": false,
    "notify_jd": false,
    "notify_amazon": false,
    "notify_gift_card": true    ← 只有这个是 true
  },
  "notes": "只要苹果礼品卡优惠"
}
```

### 示例 2：朋友关心汇率和礼品卡

**需求：**
- 朋友想知道汇率什么时候便宜（准备换汇）
- 也想知道礼品卡什么时候打折

**配置：**
```json
{
  "name": "朋友小红",
  "email": "xiaohong@163.com",
  "enabled": true,
  "role": "subscriber",
  "preferences": {
    "notify_fx": true,           ← 要汇率通知
    "notify_jd": false,
    "notify_amazon": false,
    "notify_gift_card": true     ← 要礼品卡通知
  },
  "notes": "关注汇率和礼品卡"
}
```

### 示例 3：你自己（全部通知）

**需求：**
- 你是系统主人，想接收所有通知

**配置：**
```json
{
  "name": "你的名字",
  "email": "you@gmail.com",
  "enabled": true,
  "role": "owner",
  "preferences": {
    "notify_fx": true,
    "notify_jd": true,
    "notify_amazon": true,
    "notify_gift_card": true    ← 全部 true
  },
  "notes": "系统主人"
}
```

### 示例 4：临时禁用某人

**需求：**
- 朋友暂时不想收通知（比如考试周）

**配置：**
```json
{
  "name": "朋友小李",
  "email": "xiaoli@outlook.com",
  "enabled": false,             ← 改为 false
  "role": "subscriber",
  "preferences": {
    "notify_fx": false,
    "notify_jd": false,
    "notify_amazon": false,
    "notify_gift_card": true
  },
  "notes": "考试周，暂时禁用"
}
```

**效果：** 系统会跳过这个人，不发邮件

---

## 📧 邮件效果

### 你收到的邮件

```
┌─────────────────────────────────────────┐
│  你好，你的名字！                        │
│  系统主人                                │
├─────────────────────────────────────────┤
│  🎁 Amazon 礼品卡提醒                   │
│  Apple Gift Card $100                   │
│                                         │
│  当前价格: $95.00                        │
│  面值: $100.00                          │
│  直接折扣: $5.00 (5.0% off)             │
│                                         │
│  💰 综合收益计算                        │
│  礼品卡面值       $100.00               │
│  实际支付         $95.00                │
│  当前汇率(最优)   7.1420                │
│  人民币成本       ¥678.49               │
│  礼品卡价值       ¥714.20               │
│  实际节省         ¥35.71                │
│  综合折扣率       5.00%                 │
│                                         │
│  [🔗 立即查看]                          │
└─────────────────────────────────────────┘
```

### 朋友收到的邮件

```
┌─────────────────────────────────────────┐
│  你好，朋友小明！                        │
├─────────────────────────────────────────┤
│  🎁 Amazon 礼品卡提醒                   │
│  Apple Gift Card $100                   │
│                                         │
│  当前价格: $95.00                        │
│  面值: $100.00                          │
│  直接折扣: $5.00 (5.0% off)             │
│                                         │
│  💰 综合收益计算                        │
│  （同上）                                │
│                                         │
│  [🔗 立即查看]                          │
└─────────────────────────────────────────┘
```

**区别：**
- 个性化称呼（你的名字 vs 朋友小明）
- 你的邮件会显示"系统主人"标识

---

## 🔍 工作原理

### 通知类型检测

```
系统检测到：Apple Gift Card $100 降价
    ↓
判断通知类型：gift_card
    ↓
筛选收件人：
- 检查每个人的 preferences.notify_gift_card
- 保留 true 的收件人
    ↓
发送邮件给筛选后的收件人
```

### 示例流程

**假设你的 recipients.json：**

```json
{
  "recipients": [
    {"name": "你", "email": "you@...", "enabled": true, 
     "preferences": {"notify_gift_card": true}},
    
    {"name": "朋友A", "email": "a@...", "enabled": true,
     "preferences": {"notify_gift_card": true}},
    
    {"name": "朋友B", "email": "b@...", "enabled": true,
     "preferences": {"notify_gift_card": false}},
    
    {"name": "朋友C", "email": "c@...", "enabled": false,
     "preferences": {"notify_gift_card": true}}
  ]
}
```

**系统检测到礼品卡打折：**

```
1. 读取所有收件人（4人）
2. 筛选 enabled: true（3人：你、A、B）
3. 筛选 notify_gift_card: true（2人：你、A）
4. 发送邮件给：你、A
5. 不发送给：B（不想要）、C（已禁用）
```

---

## 🎯 实际运行输出

### 控制台显示

```
💱 汇率监控
================================================
✅ 加载了 4 个收件人
当前汇率: 7.1450 (中国银行)
变化幅度: -2.1% (未达到 4% 门槛)
✅ 汇率正常，无需提醒

🛍️  Amazon 监控
================================================
🎁 检查 Amazon Reload 促销...
  未检测到 Reload 促销
🎁 检查 Gift Card 促销...
  未检测到礼品卡促销
🔍 检查 Amazon 商品: Apple Gift Card $100
  价格: $95.00 | 库存: In Stock
📧 准备发送 gift_card 类型通知给 2 个收件人
  ✅ 已发送给: 你的名字 (you@gmail.com)
  ✅ 已发送给: 朋友A (friend_a@qq.com)
  ⚠️  跳过: 朋友B (不想要此类型通知)
  ⚠️  跳过: 朋友C (已禁用)
✅ 成功发送给 2/2 个收件人
```

---

## 🛠️ 管理操作

### 添加新朋友

```bash
1. 打开 recipients.json
2. 在 "recipients" 数组末尾添加：
   {
     "name": "新朋友",
     "email": "new_friend@qq.com",
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
3. 保存文件
4. 下次运行时自动生效
```

### 修改朋友的通知偏好

```bash
1. 打开 recipients.json
2. 找到对应的朋友
3. 修改 preferences 中的值
   notify_gift_card: false → true
4. 保存文件
5. 下次运行时自动生效
```

### 暂时禁用某人

```bash
1. 打开 recipients.json
2. 找到对应的朋友
3. 修改 enabled: true → false
4. 保存文件
5. 下次运行时自动生效
```

### 永久删除某人

```bash
1. 打开 recipients.json
2. 找到对应的 {...} 对象
3. 整个删除（注意逗号）
4. 保存文件
5. 下次运行时自动生效
```

---

## ⚠️ 注意事项

### 1. JSON 格式

**常见错误：**
```json
// ❌ 错误：最后一个对象后面有逗号
{
  "recipients": [
    {...},
    {...},  ← 这个逗号要删除
  ]
}

// ✅ 正确：最后一个对象后面没有逗号
{
  "recipients": [
    {...},
    {...}
  ]
}
```

### 2. 邮箱格式

**有效的邮箱格式：**
```
✅ user@gmail.com
✅ user@qq.com
✅ user@163.com
✅ user@outlook.com
✅ user.name@company.com
❌ user@（不完整）
❌ @gmail.com（缺少用户名）
```

### 3. 环境变量兼容

**如果 recipients.json 不存在：**
```
系统会回退到环境变量 RECIPIENT_EMAIL
    ↓
保证向后兼容
    ↓
但推荐使用 recipients.json（更强大）
```

---

## 🎉 优势总结

### 对比单收件人

| 功能 | 单收件人（原来） | 多收件人（现在） |
|-----|----------------|----------------|
| **添加收件人** | 改代码 | 编辑JSON |
| **个性化称呼** | ❌ 不支持 | ✅ 支持 |
| **通知偏好** | ❌ 不支持 | ✅ 支持 |
| **临时禁用** | 改代码 | 改enabled |
| **管理难度** | 困难 | 简单 |

### 对你的好处

1. **方便管理朋友**
   - 添加/删除：只需编辑文件
   - 不用改代码
   - 不用重新部署

2. **个性化体验**
   - 每个人收到自己名字的邮件
   - 更友好

3. **灵活控制**
   - 朋友只要礼品卡通知
   - 你要所有通知
   - 各取所需

4. **代购管理**
   - 清楚知道谁要买什么
   - 系统自动记录
   - 方便对账

---

## 💰 代购场景示例

### 场景：朋友要买礼品卡

**系统通知：**
```
[邮件] 发送给：你、朋友A
标题：🎁 Amazon 礼品卡提醒
内容：Apple Gift Card $100 降到 $95
```

**朋友看到邮件：**
```
朋友："有优惠了！我要买2张"
```

**你的操作：**
```
1. 朋友先给你钱：
   ¥720 x 2 = ¥1440

2. 你用 Visa 卡买：
   $95 x 2 = $190

3. 收到礼品卡电子码

4. 发给朋友
```

**记录管理：**
```
recipients.json 中的 notes 字段：
"notes": "已代购2张 Apple GC $100，收款 ¥1440，2026-02-17"
```

---

## 🚀 未来扩展

### 可以添加的功能

1. **每人的购买记录**
   ```json
   "purchase_history": [
     {"date": "2026-02-17", "item": "Apple GC $100", "amount": 2}
   ]
   ```

2. **欠款管理**
   ```json
   "balance": -200,
   "last_payment": "2026-02-15"
   ```

3. **语言偏好**
   ```json
   "language": "zh-CN" / "en-US"
   ```

4. **通知频率**
   ```json
   "notify_frequency": "realtime" / "daily_digest"
   ```

---

## 📞 常见问题

### Q1: 如何测试配置是否正确？

```bash
python main.py --test-email
```

系统会给所有 `enabled: true` 的收件人发测试邮件。

### Q2: 朋友收不到邮件怎么办？

**检查：**
1. `recipients.json` 中 `enabled` 是否为 `true`
2. `preferences` 中对应的通知类型是否为 `true`
3. 邮箱地址是否正确
4. 检查垃圾邮件文件夹

### Q3: 可以添加多少个收件人？

理论上无限制，但：
- Brevo 免费版每天 300 封邮件
- 如果有10个收件人，每天最多触发30次通知

### Q4: 如何让朋友收到所有通知？

```json
{
  "name": "朋友",
  "email": "friend@qq.com",
  "enabled": true,
  "preferences": {
    "notify_fx": true,      ← 全部改为 true
    "notify_jd": true,
    "notify_amazon": true,
    "notify_gift_card": true
  }
}
```

---

**你的需求已经完美实现了！** 🎉

**现在你可以轻松地给朋友添加通知，帮他们一起薅羊毛！** 💰

---

**文档版本**: v1.0  
**创建日期**: 2026-02-16  
**适用系统**: v2.0+
