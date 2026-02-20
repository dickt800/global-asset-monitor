"""
全球资产监控系统 - 抽象基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BaseMonitor(ABC):
    """
    所有监控器的抽象基类
    
    子类必须实现：
    1. check() - 核心检测逻辑
    2. _should_notify() - 是否应该发送通知
    """
    
    def __init__(self, config: Dict[str, Any], name: str):
        """
        Args:
            config: 监控器的配置字典
            name: 监控器名称（用于日志）
        """
        self.config = config
        self.name = name
        self.logger = logging.getLogger(self.name)
        self.enabled = config.get('enabled', False)
        
    @abstractmethod
    def check(self) -> Optional[List[Dict[str, Any]]]:
        """
        执行监控检查
        
        Returns:
            如果需要通知，返回通知数据列表；否则返回 None
            每个通知数据应包含：
            {
                'title': '通知标题',
                'message': '通知内容',
                'url': '直达链接',
                'price_info': '价格信息',
                'level': 1-3 (紧急程度)
            }
        """
        pass
    
    @abstractmethod
    def _should_notify(self, current_value: float, last_value: Optional[float]) -> bool:
        """
        判断是否应该发送通知
        
        Args:
            current_value: 当前值（价格/汇率等）
            last_value: 上次提醒时的值
            
        Returns:
            是否应该通知
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控器状态（用于Dashboard展示）"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'last_run': None  # 子类可覆盖
        }
    
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        if not self.enabled:
            self.logger.info(f"{self.name} 已禁用")
            return False
        return True
