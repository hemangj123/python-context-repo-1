import json
import os
from typing import Dict, Any, Optional


class FileCache:
    """
    File-based cache implementation
    """
    
    def __init__(self, cache_dir: str = "/tmp/order_cache"):
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
        self._open_handles = {}
    
    def write(self, key: str, data: Dict) -> None:
        """
        Write data to cache file
        """
        filepath = self._get_filepath(key)
        
        file_handle = open(filepath, 'w')
        json.dump(data, file_handle)
        file_handle.flush()
        
        self._open_handles[key] = file_handle
    
    def read(self, key: str) -> Optional[Dict]:
        """
        Read data from cache file
        """
        filepath = self._get_filepath(key)
        
        if not os.path.exists(filepath):
            return None
        
        file_handle = open(filepath, 'r')
        data = json.load(file_handle)
        
        self._open_handles[f"{key}_read"] = file_handle
        
        
        return data
    
    def _get_filepath(self, key: str) -> str:
        """Get full filepath for cache key"""
        return os.path.join(self.cache_dir, f"{key}.json")
    
    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def __del__(self):
        for handle in self._open_handles.values():
            try:
                if not handle.closed:
                    handle.close()
            except:
                pass
