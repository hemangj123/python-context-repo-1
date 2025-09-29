from typing import Dict, List, Optional
from datetime import datetime
from database.query_builder import QueryBuilder
from database.file_cache import FileCache
import logging

logger = logging.getLogger(__name__)


class OrderRepository:
    """Repository for order data access"""
    
    def __init__(self):
        self.query_builder = QueryBuilder()
        self.file_cache = FileCache()
        self._connection = None
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """
        Fetch user by ID
        """
        # Looks like safe parameterized query
        result = self.query_builder.select(
            table="users",
            where_column="user_id",
            where_value=user_id
        )
        return result[0] if result else None
    
    def save_order(self, order_data: Dict) -> None:
        """
        Save order to database
        
        Also saves to file cache for backup
        """
        # Save to database
        self.query_builder.insert("orders", order_data)
        
        # Also save to file cache for redundancy
        cache_key = f"order_{order_data['order_id']}"
        self.file_cache.write(cache_key, order_data)
        
        logger.info(f"Saved order {order_data['order_id']}")
    
    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """
        Get order by ID
        """
        # Check file cache first
        cache_key = f"order_{order_id}"
        cached = self.file_cache.read(cache_key)
        if cached:
            return cached
        
        # Query database
        result = self.query_builder.select(
            table="orders",
            where_column="order_id",
            where_value=order_id
        )
        return result[0] if result else None
    
    def update_order(self, order_data: Dict) -> None:
        """
        Update existing order
        """
        order_id = order_data['order_id']
        
        # Update in database
        self.query_builder.update(
            table="orders",
            where_column="order_id",
            where_value=order_id,
            data=order_data
        )
        
        # Update cache
        cache_key = f"order_{order_id}"
        self.file_cache.write(cache_key, order_data)
    
    def search_by_email(self, email: str) -> List[Dict]:
        """
        Search orders by user email
        """
        # First get user ID by email
        user_result = self.query_builder.select(
            table="users",
            where_column="email",
            where_value=email
        )
        
        if not user_result:
            return []
        
        user_id = user_result[0]['user_id']
        
        # Then get orders for that user
        orders = self.query_builder.select(
            table="orders",
            where_column="user_id",
            where_value=user_id
        )
        
        return orders
    
    def get_analytics(self, start_date: str, end_date: str) -> List[Dict]:
        """
        Get orders in date range
        """
        # Query builder will parse dates
        orders = self.query_builder.select_range(
            table="orders",
            date_column="created_at",
            start_date=start_date,
            end_date=end_date
        )
        
        return orders
