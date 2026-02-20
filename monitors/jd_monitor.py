"""
京东自营监控模块 - 专为京东H5页面优化
"""
import re
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from monitors.base_monitor import BaseMonitor
from utils.persistence import PersistenceManager
from utils.anti_crawler import AntiCrawler


class JDMonitor(BaseMonitor):
    """
    京东自营商品监控器
    
    核心特性：
    1. 监控 H5 移动端页面（规避PC端反爬）
    2. 检测"自营"、"百亿补贴"、"秒杀"标识
    3. 价格低于心理价位时触发 Level 2 提醒
    4. 随机延迟 + 移动端 Header
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config, 'JDMonitor')
        self.persistence = PersistenceManager()
        self.products = config.get('products', [])
        self.session = AntiCrawler.get_jd_session()
        
    def check(self) -> Optional[List[Dict[str, Any]]]:
        """执行京东商品监控"""
        if not self.validate_config():
            return None
        
        notifications = []
        
        for product in self.products:
            sku_id = product['sku_id']
            expected_price = product['expected_price']
            name = product.get('name', f'商品 {sku_id}')
            
            self.logger.info(f"🔍 检查京东商品: {name} (SKU: {sku_id})")
            
            # 随机延迟（模拟人类行为）
            AntiCrawler.random_delay(1.5, 3.5)
            
            # 抓取商品信息
            product_info = self._fetch_product_info(sku_id)
            
            if product_info is None:
                self.logger.error(f"无法获取 SKU {sku_id} 的信息")
                continue
            
            current_price = product_info['price']
            in_stock = product_info['in_stock']
            is_self_operated = product_info['is_self_operated']
            has_subsidy = product_info['has_subsidy']
            
            self.logger.info(
                f"  价格: ¥{current_price:.2f} | 库存: {'有货' if in_stock else '无货'} | "
                f"自营: {'是' if is_self_operated else '否'} | 补贴: {'是' if has_subsidy else '否'}"
            )
            
            # 判断是否需要通知
            should_notify = False
            notify_level = 1
            notify_reasons = []
            
            # 1. 价格低于心理价位
            if current_price <= expected_price and in_stock:
                should_notify = True
                notify_level = 2
                price_diff = expected_price - current_price
                notify_reasons.append(f"💰 价格达标 (低于心理价位 ¥{price_diff:.2f})")
            
            # 2. 百亿补贴/秒杀
            if has_subsidy and in_stock:
                should_notify = True
                notify_level = 3
                notify_reasons.append("🔥 百亿补贴/秒杀活动")
            
            # 3. 价格低于上次提醒价格
            last_price = self.persistence.get_last_value(f'jd_{sku_id}')
            if last_price and current_price < last_price and in_stock:
                should_notify = True
                notify_reasons.append(f"📉 价格下降 (¥{last_price:.2f} → ¥{current_price:.2f})")
            
            # 4. 非自营商品警告
            if not is_self_operated:
                notify_reasons.append("⚠️ 非自营商品")
                notify_level = max(notify_level - 1, 1)
            
            # 发送通知
            if should_notify:
                price_diff_text = f"¥{expected_price - current_price:.2f}" if current_price <= expected_price else f"+¥{current_price - expected_price:.2f}"
                
                notifications.append({
                    'title': f'🛒 京东提醒 - {name}',
                    'message': f"""
<h2>{name}</h2>
<p><strong>SKU ID:</strong> {sku_id}</p>
<p><strong>当前价格:</strong> <span style="color: {'green' if current_price <= expected_price else 'red'}; font-size: 24px;">¥{current_price:.2f}</span></p>
<p><strong>心理价位:</strong> ¥{expected_price:.2f}</p>
<p><strong>价差:</strong> <span style="color: {'green' if current_price <= expected_price else 'red'};">{price_diff_text}</span></p>
<p><strong>库存状态:</strong> {'✅ 有货' if in_stock else '❌ 无货'}</p>
<p><strong>商品属性:</strong> {'✅ 京东自营' if is_self_operated else '⚠️ 非自营'}</p>
<hr>
<h3>触发原因：</h3>
<ul>
{''.join([f'<li>{reason}</li>' for reason in notify_reasons])}
</ul>
                    """,
                    'url': f'https://item.jd.com/{sku_id}.html',
                    'price_info': f'¥{current_price:.2f} (vs ¥{expected_price:.2f})',
                    'level': notify_level
                })
                
                # 更新状态
                self.persistence.update_value(
                    f'jd_{sku_id}',
                    current_price,
                    {
                        'name': name,
                        'in_stock': in_stock,
                        'is_self_operated': is_self_operated,
                        'has_subsidy': has_subsidy
                    }
                )
        
        return notifications if notifications else None
    
    def _fetch_product_info(self, sku_id: str) -> Optional[Dict[str, Any]]:
        """
        抓取京东H5商品信息
        
        Args:
            sku_id: 商品SKU ID
            
        Returns:
            商品信息字典或 None
        """
        # 使用移动端 URL
        mobile_url = f'https://item.m.jd.com/product/{sku_id}.html'
        
        try:
            # 使用带移动端 Header 的 Session
            headers = AntiCrawler.get_mobile_headers(referer='https://m.jd.com/')
            response = self.session.get(mobile_url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                self.logger.error(f"请求失败: HTTP {response.status_code}")
                return None
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取价格（多种可能的选择器）
            price = self._extract_price(soup, sku_id)
            if price is None:
                return None
            
            # 检测库存状态
            in_stock = self._check_stock(soup)
            
            # 检测是否自营
            is_self_operated = self._check_self_operated(soup)
            
            # 检测百亿补贴/秒杀
            has_subsidy = self._check_subsidy(soup)
            
            return {
                'price': price,
                'in_stock': in_stock,
                'is_self_operated': is_self_operated,
                'has_subsidy': has_subsidy
            }
            
        except Exception as e:
            self.logger.error(f"抓取失败: {e}")
            return None
    
    def _extract_price(self, soup: BeautifulSoup, sku_id: str) -> Optional[float]:
        """
        提取价格（多种方法尝试）
        
        Args:
            soup: BeautifulSoup 对象
            sku_id: SKU ID
            
        Returns:
            价格或 None
        """
        # 方法1: 从 JavaScript 变量中提取
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and 'price' in script.string:
                # 匹配类似 "price":"299.00" 的模式
                match = re.search(r'"price"\s*:\s*"?(\d+\.?\d*)"?', script.string)
                if match:
                    return float(match.group(1))
        
        # 方法2: 从 HTML 元素中提取
        price_elements = soup.select('.p-price, .price, .jd-price')
        for elem in price_elements:
            text = elem.get_text(strip=True)
            match = re.search(r'(\d+\.?\d*)', text)
            if match:
                return float(match.group(1))
        
        # 方法3: 使用价格 API（更可靠）
        try:
            price_api_url = f'https://p.3.cn/prices/mgets?skuIds=J_{sku_id}'
            headers = AntiCrawler.get_mobile_headers()
            response = self.session.get(price_api_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    price_str = data[0].get('p', data[0].get('op'))
                    if price_str:
                        return float(price_str)
        except Exception as e:
            self.logger.warning(f"价格API请求失败: {e}")
        
        return None
    
    def _check_stock(self, soup: BeautifulSoup) -> bool:
        """
        检测库存状态
        
        Args:
            soup: BeautifulSoup 对象
            
        Returns:
            是否有货
        """
        # 检测"无货"、"缺货"等关键词
        out_of_stock_keywords = ['无货', '缺货', '暂时缺货', '已售罄', '下架']
        page_text = soup.get_text()
        
        for keyword in out_of_stock_keywords:
            if keyword in page_text:
                return False
        
        return True
    
    def _check_self_operated(self, soup: BeautifulSoup) -> bool:
        """
        检测是否为京东自营
        
        Args:
            soup: BeautifulSoup 对象
            
        Returns:
            是否自营
        """
        page_text = soup.get_text()
        
        # 检测"自营"关键词
        self_operated_keywords = ['京东自营', '自营']
        
        for keyword in self_operated_keywords:
            if keyword in page_text:
                return True
        
        return False
    
    def _check_subsidy(self, soup: BeautifulSoup) -> bool:
        """
        检测是否有补贴活动
        
        Args:
            soup: BeautifulSoup 对象
            
        Returns:
            是否有补贴
        """
        page_text = soup.get_text()
        
        # 检测活动关键词
        subsidy_keywords = ['百亿补贴', '秒杀', '限时抢购', '特价']
        
        for keyword in subsidy_keywords:
            if keyword in page_text:
                return True
        
        return False
    
    def _should_notify(self, current_value: float, last_value: Optional[float]) -> bool:
        """判断是否应该通知"""
        # 京东监控的通知逻辑在 check() 方法中已处理
        return True
