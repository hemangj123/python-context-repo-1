from typing import Dict
from network.http_client import HTTPClient
import logging

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Process payments via external payment gateway"""
    
    def __init__(self):
        self.http_client = HTTPClient()
        self.api_key = "sk_test_12345"
        self.base_url = "https://api.paymentgateway.com"
    
    def charge(self, amount: float, token: str, user_id: str) -> Dict:
        """
        Charge payment
        """
        endpoint = f"{self.base_url}/charges"
        
        payload = {
            'amount': int(amount * 100),  # Convert to cents
            'currency': 'usd',
            'source': token,
            'metadata': {'user_id': user_id}
        }
        
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        response = self.http_client.post(endpoint, payload, headers)
        
        return {
            'success': response.get('status') == 'succeeded',
            'payment_id': response.get('id')
        }
    
    def refund(self, payment_id: str, amount: float) -> Dict:
        """
        Refund a payment
       
        """
        endpoint = f"{self.base_url}/refunds"
        
        payload = {
            'charge': payment_id,
            'amount': int(amount * 100)
        }
        
        headers = {'Authorization': f'Bearer {self.api_key}'}

        response = self.http_client.post(endpoint, payload, headers)
        
        return {
            'success': response.get('status') == 'succeeded',
            'refund_id': response.get('id')
        }
