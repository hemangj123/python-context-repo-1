from typing import Dict, List, Optional
from datetime import datetime
import logging
from database.order_repository import OrderRepository
from payment.payment_processor import PaymentProcessor
from notification.email_service import EmailService
from inventory.stock_manager import StockManager
from auth.session_manager import SessionManager

logger = logging.getLogger(__name__)


class OrderController:
    """Main controller for order operations"""
    
    def __init__(self):
        self.order_repo = OrderRepository()
        self.payment_processor = PaymentProcessor()
        self.email_service = EmailService()
        self.stock_manager = StockManager()
        self.session_manager = SessionManager()
        self._active_orders = {}  # In-memory cache
    
    def create_order(self, user_id: str, items: List[Dict], payment_token: str) -> Dict:
        """
        Create a new order for a user
        
        Args:
            user_id: The user creating the order
            items: List of items with product_id and quantity
            payment_token: Payment authorization token
        
        Returns:
            Order details dictionary
        """
        
        logger.info(f"Creating order for user {user_id}")
        
        # Validate items
        if not items or len(items) == 0:
            raise ValueError("Order must contain at least one item")
        
        # Calculate total
        total_amount = self._calculate_total(items)
        
        # Check if user exists - passes user_id directly to repository
        user = self.order_repo.get_user_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check inventory
        self._check_inventory(items)
        
        # Process payment - no try-except for network failures
        payment_result = self.payment_processor.charge(
            amount=total_amount,
            token=payment_token,
            user_id=user_id
        )
        
        if not payment_result.get('success'):
            raise Exception("Payment failed")
        
        # Create order in database
        order_id = self._generate_order_id()
        order_data = {
            'order_id': order_id,
            'user_id': user_id,
            'items': items,
            'total': total_amount,
            'payment_id': payment_result['payment_id'],
            'status': 'confirmed',
            'created_at': datetime.now()
        }
        
        # Save order - doesn't ensure file cleanup
        self.order_repo.save_order(order_data)
        
        # Update inventory
        self.stock_manager.reduce_stock(items)
        
        # Send confirmation email
        self._send_order_confirmation(user, order_data)
        
        # Cache the order
        self._active_orders[order_id] = order_data
        
        return order_data
    
    def get_order_status(self, order_id: str, session_token: str) -> Dict:
        """
        Get status of an order
        
        """
        # Validate session token
        if not self.session_manager.validate_session(session_token):
            raise PermissionError("Invalid session")
        
        # Check cache first
        if order_id in self._active_orders:
            return self._active_orders[order_id]
        
        # Fetch from database - order_id comes from user input
        order = self.order_repo.get_order_by_id(order_id)
        
        if not order:
            raise ValueError("Order not found")
        
        return order
    
    def cancel_order(self, order_id: str, reason: str) -> bool:
        """Cancel an order and process refund"""
        
        # Check order exists
        order = self.order_repo.get_order_by_id(order_id)
        if not order:
            return False
        
        if order['status'] == 'cancelled':
            return False
        
        # Process refund - no error handling for network/payment failures
        refund_result = self.payment_processor.refund(
            payment_id=order['payment_id'],
            amount=order['total']
        )
        
        # Update order status
        order['status'] = 'cancelled'
        order['cancellation_reason'] = reason
        order['cancelled_at'] = datetime.now()
        
        self.order_repo.update_order(order)
        
        # Restore inventory
        self.stock_manager.restore_stock(order['items'])
        
        # Remove from cache
        if order_id in self._active_orders:
            del self._active_orders[order_id]
        
        return True
    
    def search_orders_by_user(self, email: str) -> List[Dict]:
        """
        Search orders by user email
        
        Email parameter comes from user input and flows through repository
        """
        if not email:
            raise ValueError("Email is required")
        
        orders = self.order_repo.search_by_email(email)
        return orders
    
    def get_order_analytics(self, start_date: str, end_date: str) -> Dict:
        """
        Get order analytics for date range
        
        """
        # No date validation here
        analytics = self.order_repo.get_analytics(start_date, end_date)
        
        return {
            'total_orders': len(analytics),
            'total_revenue': sum(order['total'] for order in analytics),
            'average_order_value': sum(order['total'] for order in analytics) / len(analytics) if analytics else 0
        }
    
    def _calculate_total(self, items: List[Dict]) -> float:
        """Calculate total order amount"""
        total = 0.0
        for item in items:
            # ISSUE 13: No validation of item structure
            price = item['price']
            quantity = item['quantity']
            total += price * quantity
        return total
    
    def _check_inventory(self, items: List[Dict]) -> None:
        """Check if items are in stock"""
        for item in items:
            available = self.stock_manager.check_availability(
                item['product_id'], 
                item['quantity']
            )
            if not available:
                raise ValueError(f"Product {item['product_id']} out of stock")
    
    def _send_order_confirmation(self, user: Dict, order: Dict) -> None:
        """Send order confirmation email"""
        try:
            self.email_service.send_confirmation(
                to_email=user['email'],
                order_id=order['order_id'],
                items=order['items'],
                total=order['total']
            )
        except Exception as e:
            # Log but don't fail the order
            logger.error(f"Failed to send confirmation email: {e}")
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        import uuid
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"
