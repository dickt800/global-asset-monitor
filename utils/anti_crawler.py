"""
反爬虫工具集
"""
import random
import time
from typing import Dict, Optional
import requests
from fake_useragent import UserAgent


class AntiCrawler:
    """反爬虫策略管理器"""
    
    # 移动端 User-Agent 池（京东专用）
    MOBILE_USER_AGENTS = [
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/117.0.5938.117 Mobile/15E148 Safari/604.1',
    ]
    
    # PC端 User-Agent 池（Amazon专用）
    PC_USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ]
    
    def __init__(self):
        self.ua = UserAgent()
    
    @staticmethod
    def get_mobile_headers(referer: Optional[str] = None) -> Dict[str, str]:
        """
        获取移动端请求头（京东专用）
        
        Args:
            referer: 可选的 Referer
        """
        headers = {
            'User-Agent': random.choice(AntiCrawler.MOBILE_USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        if referer:
            headers['Referer'] = referer
            
        return headers
    
    @staticmethod
    def get_pc_headers(referer: Optional[str] = None) -> Dict[str, str]:
        """
        获取PC端请求头（Amazon专用）
        
        Args:
            referer: 可选的 Referer
        """
        headers = {
            'User-Agent': random.choice(AntiCrawler.PC_USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'DNT': '1',
        }
        
        if referer:
            headers['Referer'] = referer
            
        return headers
    
    @staticmethod
    def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
        """
        随机延迟（模拟人类行为）
        
        Args:
            min_seconds: 最小延迟（秒）
            max_seconds: 最大延迟（秒）
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    @staticmethod
    def safe_request(url: str, headers: Dict[str, str], 
                     timeout: int = 10, max_retries: int = 3) -> Optional[requests.Response]:
        """
        带重试的安全请求
        
        Args:
            url: 请求URL
            headers: 请求头
            timeout: 超时时间
            max_retries: 最大重试次数
            
        Returns:
            Response对象或None
        """
        for attempt in range(max_retries):
            try:
                # 随机延迟
                if attempt > 0:
                    AntiCrawler.random_delay(2.0, 5.0)
                
                response = requests.get(url, headers=headers, timeout=timeout)
                
                # 检查是否被反爬
                if response.status_code == 403:
                    print(f"⚠️  请求被拒绝 (403)，尝试 {attempt + 1}/{max_retries}")
                    continue
                    
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                print(f"⚠️  请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    return None
        
        return None
    
    @staticmethod
    def get_jd_session() -> requests.Session:
        """
        创建京东专用 Session（带 Cookie 池）
        
        Returns:
            配置好的 Session 对象
        """
        session = requests.Session()
        
        # 设置移动端 User-Agent
        session.headers.update(AntiCrawler.get_mobile_headers())
        
        # 模拟真实浏览器的 Cookie
        session.cookies.set('wlfstk_smdl', 'random_token_' + str(random.randint(100000, 999999)))
        
        return session
