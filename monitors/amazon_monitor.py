"""
Amazon 商品监控模块 - 包含礼品卡促销监控
"""
import re
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from monitors.base_monitor import BaseMonitor
from utils.persistence import PersistenceManager
from utils.anti_crawler import AntiCrawler


class AmazonMonitor(BaseMonitor):
    """
    Amazon 商品监控器
    
    核心特性：
    1. 监控特定商品（如 Apple Gift Card）
    2. 监控 Amazon Reload 促销（Get $X credit）
    3. 监控 Gift Card Promotions 页面
    4. 计算礼品卡折扣 + 汇率优惠的综合收益
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, 'AmazonMonitor')
        self.persistence = PersistenceManager()
        self.products = config.get('products', [])
        self.keywords = config.get('keywords', [])
        self.region = config.get('region', 'us')  # us/uk/de
        self.monitor_gift_cards = config.get('monitor_gift_cards', True)
        self.monitor_reload = config.get('monitor_reload', True)
        
    def check(self) -> Optional[List[Dict[str, Any]]]:
        """执行 Amazon 商品监控"""
        if not self.validate_config():
            return None
        
        notifications = []
        
        # 1. 监控 Amazon Reload 促销
        if self.monitor_reload:
            self.logger.info("🎁 检查 Amazon Reload 促销...")
            reload_notification = self._check_reload_promotions()
            if reload_notification:
                notifications.append(reload_notification)
        
        # 2. 监控 Gift Card Promotions 页面
        if self.monitor_gift_cards:
            self.logger.info("🎁 检查 Gift Card 促销...")
            gift_card_notifications = self._check_gift_card_promotions()
            if gift_card_notifications:
                notifications.extend(gift_card_notifications)
        
        # 3. 监控具体商品（Apple Gift Card 等）
        for product in self.products:
            asin = product.get('asin')
            url = product.get('url')
            expected_price = product.get('expected_price')
            name = product.get('name', f'Product {asin or "Unknown"}')
            is_gift_card = product.get('is_gift_card', False)
            
            if not asin and not url:
                self.logger.warning(f"商品 {name} 缺少 ASIN 或 URL")
                continue
            
            self.logger.info(f"🔍 检查 Amazon 商品: {name}")
            
            # 随机延迟
            AntiCrawler.random_delay(2.0, 4.0)
            
            # 抓取商品信息
            if url:
                product_url = url
            else:
                product_url = self._build_product_url(asin)
            
            product_info = self._fetch_product_info(product_url)
            
            if product_info is None:
                self.logger.error(f"无法获取商品信息: {name}")
                continue
            
            current_price = product_info['price']
            availability = product_info['availability']
            
            self.logger.info(f"  价格: ${current_price:.2f} | 库存: {availability}")
            
            # 判断是否通知
            if expected_price and current_price <= expected_price and availability:
                price_diff = expected_price - current_price
                discount_percent = (price_diff / expected_price) * 100
                
                # 如果是礼品卡，计算综合收益
                comprehensive_info = ""
                if is_gift_card and current_price < expected_price:
                    comprehensive_info = self._calculate_comprehensive_discount(
                        current_price, 
                        expected_price,
                        is_gift_card=True
                    )
                
                notifications.append({
                    'title': f'🎁 Amazon 礼品卡提醒 - {name}' if is_gift_card else f'🛒 Amazon 提醒 - {name}',
                    'message': f"""
<h2>{name}</h2>
<p><strong>当前价格:</strong> <span style="color: green; font-size: 24px;">${current_price:.2f}</span></p>
<p><strong>面值/目标价:</strong> ${expected_price:.2f}</p>
<p><strong>直接折扣:</strong> <span style="color: green;">${price_diff:.2f} ({discount_percent:.1f}% off)</span></p>
<p><strong>库存:</strong> {availability}</p>
{comprehensive_info}
                    """,
                    'url': product_url,
                    'price_info': f'${current_price:.2f} (vs ${expected_price:.2f})',
                    'level': 3 if discount_percent >= 5 else 2
                })
                
                # 更新状态
                self.persistence.update_value(
                    f'amazon_{asin or url}',
                    current_price,
                    {'name': name, 'availability': availability}
                )
        
        # 4. 关键词搜索监控（扩展功能）
        for keyword_config in self.keywords:
            keyword = keyword_config['keyword']
            max_price = keyword_config.get('max_price')
            
            self.logger.info(f"🔍 搜索关键词: {keyword}")
            # TODO: 实现关键词搜索逻辑
        
        return notifications if notifications else None
    
    def _check_reload_promotions(self) -> Optional[Dict[str, Any]]:
        """
        检查 Amazon Reload 促销
        
        Returns:
            通知数据或 None
        """
        try:
            # Amazon Reload 页面
            url = 'https://www.amazon.com/asv/reload'
            headers = AntiCrawler.get_pc_headers(referer='https://www.amazon.com/')
            
            response = AntiCrawler.safe_request(url, headers, timeout=15)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            
            # 检测促销关键词
            promotion_keywords = [
                r'Get \$(\d+) credit',
                r'Get \$(\d+) promotional credit',
                r'\$(\d+) bonus',
                r'Earn \$(\d+)',
                r'Receive \$(\d+)'
            ]
            
            for pattern in promotion_keywords:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    credit_amount = int(match.group(1))
                    
                    # 检查是否已经通知过
                    last_credit = self.persistence.get_last_value('amazon_reload_credit')
                    if last_credit and last_credit == credit_amount:
                        self.logger.info(f"  Reload 促销 ${credit_amount} 已通知过，跳过")
                        return None
                    
                    self.logger.info(f"  🎉 发现 Reload 促销: Get ${credit_amount} credit")
                    
                    # 计算综合收益
                    comprehensive_info = self._calculate_reload_benefit(credit_amount)
                    
                    # 更新状态
                    self.persistence.update_value(
                        'amazon_reload_credit',
                        credit_amount,
                        {'promotion_text': match.group(0)}
                    )
                    
                    return {
                        'title': f'🎉 Amazon Reload 促销 - Get ${credit_amount} Credit',
                        'message': f"""
<h2>Amazon Reload 促销活动</h2>
<p><strong>🎁 促销内容:</strong> {match.group(0)}</p>
<p><strong>💰 奖励金额:</strong> <span style="color: green; font-size: 24px;">${credit_amount}</span></p>
<hr>
<h3>⚠️ 重要提示（中国大陆用户）</h3>
<ul>
    <li>Amazon Reload 通常需要<strong>美国银行账户</strong>（Checking Account）</li>
    <li>需要<strong>美国地址</strong>才能参与</li>
    <li>如果你没有美国银行卡，可能<strong>无法参与</strong>此活动</li>
</ul>
<hr>
{comprehensive_info}
<p><em>⚠️ 建议：先确认你的账户是否符合参与条件</em></p>
                        """,
                        'url': url,
                        'price_info': f'Get ${credit_amount} credit',
                        'level': 2
                    }
            
            self.logger.info("  未检测到 Reload 促销")
            return None
            
        except Exception as e:
            self.logger.error(f"检查 Reload 促销失败: {e}")
            return None
    
    def _check_gift_card_promotions(self) -> List[Dict[str, Any]]:
        """
        检查 Gift Card Promotions 页面
        
        Returns:
            通知数据列表
        """
        notifications = []
        
        try:
            # Gift Card Promotions 页面
            url = 'https://www.amazon.com/gcpromotions'
            headers = AntiCrawler.get_pc_headers(referer='https://www.amazon.com/')
            
            response = AntiCrawler.safe_request(url, headers, timeout=15)
            if not response:
                return notifications
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 查找促销信息
            promo_sections = soup.select('.a-section')
            
            for section in promo_sections:
                text = section.get_text()
                
                # 检测促销关键词
                if any(keyword in text.lower() for keyword in ['bonus', 'credit', 'save', 'discount']):
                    # 提取促销详情
                    promo_text = text.strip()[:200]  # 限制长度
                    
                    # 检查是否已通知
                    promo_hash = hash(promo_text)
                    last_hash = self.persistence.get_last_value(f'amazon_gc_promo_{promo_hash}')
                    
                    if last_hash:
                        continue
                    
                    self.logger.info(f"  🎉 发现礼品卡促销: {promo_text[:50]}...")
                    
                    notifications.append({
                        'title': '🎁 Amazon Gift Card 促销活动',
                        'message': f"""
<h2>礼品卡促销活动</h2>
<p><strong>促销内容:</strong></p>
<p>{promo_text}</p>
<hr>
<h3>⚠️ 中国大陆用户提示</h3>
<p>请仔细阅读促销条款，确认是否需要：</p>
<ul>
    <li>美国银行账户</li>
    <li>美国地址</li>
    <li>Prime 会员资格</li>
</ul>
                        """,
                        'url': url,
                        'price_info': 'Gift Card Promotion',
                        'level': 2
                    })
                    
                    # 更新状态
                    self.persistence.update_value(
                        f'amazon_gc_promo_{promo_hash}',
                        1,
                        {'text': promo_text}
                    )
            
            if not notifications:
                self.logger.info("  未检测到礼品卡促销")
            
            return notifications
            
        except Exception as e:
            self.logger.error(f"检查礼品卡促销失败: {e}")
            return notifications
    
    def _calculate_comprehensive_discount(self, current_price: float, 
                                         face_value: float, 
                                         is_gift_card: bool = True) -> str:
        """
        计算综合折扣（礼品卡折扣 + 汇率优惠）
        
        Args:
            current_price: 当前价格
            face_value: 面值
            is_gift_card: 是否为礼品卡
            
        Returns:
            综合收益的 HTML 字符串
        """
        if not is_gift_card or current_price >= face_value:
            return ""
        
        # 1. 礼品卡直接折扣
        card_discount = face_value - current_price
        card_discount_percent = (card_discount / face_value) * 100
        
        # 2. 获取当前汇率（尝试从持久化中读取）
        from utils.persistence import PersistenceManager
        pm = PersistenceManager()
        
        # 尝试获取最优银行汇率
        fx_data = pm.load_state().get('fx_USD_CNY_best')
        if fx_data and isinstance(fx_data, dict):
            current_rate = fx_data.get('value', 7.20)  # 默认 7.20
        else:
            current_rate = 7.20  # 默认汇率
        
        # 3. 计算人民币成本
        cny_cost = current_price * current_rate
        cny_face_value = face_value * current_rate
        cny_saved = cny_face_value - cny_cost
        
        # 4. 综合收益率
        total_discount_percent = (cny_saved / cny_face_value) * 100
        
        html = f"""
<hr>
<h3>💰 综合收益计算</h3>
<table style="border-collapse: collapse; width: 100%;">
    <tr style="background-color: #f0f0f0;">
        <th style="padding: 8px; border: 1px solid #ddd;">项目</th>
        <th style="padding: 8px; border: 1px solid #ddd;">金额</th>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;">礼品卡面值</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${face_value:.2f}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;">实际支付</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${current_price:.2f}</td>
    </tr>
    <tr style="background-color: #e8f5e9;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>直接折扣</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;"><strong>${card_discount:.2f} ({card_discount_percent:.1f}%)</strong></td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;" colspan="2"></td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;">当前汇率（最优银行）</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{current_rate:.4f}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;">人民币成本</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">¥{cny_cost:.2f}</td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;">礼品卡人民币价值</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">¥{cny_face_value:.2f}</td>
    </tr>
    <tr style="background-color: #fff3e0;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>实际节省（人民币）</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;"><strong>¥{cny_saved:.2f}</strong></td>
    </tr>
    <tr style="background-color: #e3f2fd;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>综合折扣率</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;"><strong>{total_discount_percent:.2f}%</strong></td>
    </tr>
</table>
<br>
<p><strong>🎯 购买建议:</strong></p>
<ul>
    <li>如果你计划在 Amazon 购物，现在是好时机</li>
    <li>购买礼品卡后，可以用于任何 Amazon 商品</li>
    <li>实现"折上折"效果（礼品卡折扣 + 商品折扣）</li>
</ul>
"""
        
        return html
    
    def _calculate_reload_benefit(self, credit_amount: int) -> str:
        """
        计算 Reload 促销的收益
        
        Args:
            credit_amount: 奖励金额
            
        Returns:
            收益说明的 HTML 字符串
        """
        # 假设最低 Reload 金额为 $100
        min_reload = 100
        benefit_percent = (credit_amount / min_reload) * 100
        
        # 获取当前汇率
        from utils.persistence import PersistenceManager
        pm = PersistenceManager()
        
        fx_data = pm.load_state().get('fx_USD_CNY_best')
        if fx_data and isinstance(fx_data, dict):
            current_rate = fx_data.get('value', 7.20)
        else:
            current_rate = 7.20
        
        cny_credit = credit_amount * current_rate
        
        html = f"""
<h3>💰 收益计算（假设 Reload ${min_reload}）</h3>
<table style="border-collapse: collapse; width: 100%;">
    <tr style="background-color: #f0f0f0;">
        <th style="padding: 8px; border: 1px solid #ddd;">项目</th>
        <th style="padding: 8px; border: 1px solid #ddd;">金额</th>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;">Reload 金额</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">${min_reload}</td>
    </tr>
    <tr style="background-color: #e8f5e9;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>获得奖励</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;"><strong>${credit_amount} ({benefit_percent:.0f}%)</strong></td>
    </tr>
    <tr>
        <td style="padding: 8px; border: 1px solid #ddd;">当前汇率</td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;">{current_rate:.4f}</td>
    </tr>
    <tr style="background-color: #fff3e0;">
        <td style="padding: 8px; border: 1px solid #ddd;"><strong>奖励价值（人民币）</strong></td>
        <td style="padding: 8px; border: 1px solid #ddd; text-align: right;"><strong>¥{cny_credit:.2f}</strong></td>
    </tr>
</table>
"""
        
        return html
    
    def _build_product_url(self, asin: str) -> str:
        """
        构建商品 URL
        
        Args:
            asin: Amazon ASIN
            
        Returns:
            完整 URL
        """
        domain_map = {
            'us': 'amazon.com',
            'uk': 'amazon.co.uk',
            'de': 'amazon.de',
            'jp': 'amazon.co.jp'
        }
        
        domain = domain_map.get(self.region, 'amazon.com')
        return f'https://www.{domain}/dp/{asin}'
    
    def _fetch_product_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        抓取 Amazon 商品信息
        
        Args:
            url: 商品 URL
            
        Returns:
            商品信息字典或 None
        """
        try:
            headers = AntiCrawler.get_pc_headers(referer='https://www.amazon.com/')
            response = AntiCrawler.safe_request(url, headers)
            
            if response is None:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取价格
            price = self._extract_price(soup)
            
            # 提取库存信息
            availability = self._extract_availability(soup)
            
            return {
                'price': price,
                'availability': availability
            }
            
        except Exception as e:
            self.logger.error(f"抓取失败: {e}")
            return None
    
    def _extract_price(self, soup: BeautifulSoup) -> float:
        """
        提取价格
        
        Args:
            soup: BeautifulSoup 对象
            
        Returns:
            价格
        """
        # 多种价格选择器
        price_selectors = [
            '.a-price .a-offscreen',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-price-whole'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # 移除货币符号和逗号
                price_text = re.sub(r'[^\d.]', '', price_text)
                try:
                    return float(price_text)
                except ValueError:
                    continue
        
        return 0.0
    
    def _extract_availability(self, soup: BeautifulSoup) -> str:
        """
        提取库存信息
        
        Args:
            soup: BeautifulSoup 对象
            
        Returns:
            库存状态
        """
        availability_elem = soup.select_one('#availability span')
        if availability_elem:
            return availability_elem.get_text(strip=True)
        
        return 'Unknown'
    
    def _should_notify(self, current_value: float, last_value: Optional[float]) -> bool:
        """判断是否应该通知"""
        if last_value is None:
            return True
        
        return current_value < last_value
