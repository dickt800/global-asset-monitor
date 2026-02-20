"""
状态持久化管理
"""
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime


class PersistenceManager:
    """状态持久化管理器"""
    
    def __init__(self, file_path: str = 'last_check.json'):
        """
        Args:
            file_path: 状态文件路径
        """
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """确保状态文件存在"""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def load_state(self) -> Dict[str, Any]:
        """
        加载状态
        
        Returns:
            状态字典
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  加载状态失败: {e}")
            return {}
    
    def save_state(self, state: Dict[str, Any]):
        """
        保存状态
        
        Args:
            state: 状态字典
        """
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存状态失败: {e}")
    
    def get_last_value(self, key: str) -> Optional[float]:
        """
        获取上次的值
        
        Args:
            key: 键名（如 'fx_usd_cny', 'jd_100012345678'）
            
        Returns:
            上次的值或 None
        """
        state = self.load_state()
        item = state.get(key)
        
        if item and isinstance(item, dict):
            return item.get('value')
        return None
    
    def update_value(self, key: str, value: float, metadata: Optional[Dict[str, Any]] = None):
        """
        更新值
        
        Args:
            key: 键名
            value: 新值
            metadata: 额外的元数据（如商品名称、URL等）
        """
        state = self.load_state()
        
        state[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.save_state(state)
    
    def should_notify(self, key: str, current_value: float, 
                     comparison: str = 'lower') -> bool:
        """
        判断是否应该通知（基于上次提醒的值）
        
        Args:
            key: 键名
            current_value: 当前值
            comparison: 比较方式 ('lower' 或 'higher')
            
        Returns:
            是否应该通知
        """
        last_value = self.get_last_value(key)
        
        # 首次检测，直接通知
        if last_value is None:
            return True
        
        # 价格更低时通知（适用于商品价格）
        if comparison == 'lower':
            return current_value < last_value
        
        # 价格更高时通知（适用于汇率贬值提醒）
        elif comparison == 'higher':
            return current_value > last_value
        
        return False
    
    def get_history(self, key: str, limit: int = 10) -> list:
        """
        获取历史记录（扩展功能，可用于趋势分析）
        
        Args:
            key: 键名
            limit: 返回的记录数量
            
        Returns:
            历史记录列表
        """
        # 当前版本只存储最新值，此方法为未来扩展预留
        state = self.load_state()
        item = state.get(key)
        
        if item:
            return [item]
        return []
    
    def clear_key(self, key: str):
        """
        清除指定键的状态
        
        Args:
            key: 键名
        """
        state = self.load_state()
        if key in state:
            del state[key]
            self.save_state(state)
    
    def clear_all(self):
        """清除所有状态"""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
