"""
Logger Middleware for Campus Notification System
Provides structured logging for all API requests and operations
"""

import logging
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger
import os


class NotificationLogger:
    """Custom logger for the notification system"""
    
    def __init__(self, name: str = "NotificationSystem"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # File handler with JSON format
        file_handler = logging.FileHandler('logs/notification_system.log')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler with JSON format
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # JSON formatter
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(request_id)s %(user_id)s %(endpoint)s %(duration_ms)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_api_request(self, method: str, endpoint: str, request_id: str, 
                       user_id: str = None, payload: dict = None):
        """Log incoming API request"""
        extra = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'name': 'NotificationSystem',
            'request_id': request_id,
            'user_id': user_id or 'anonymous',
            'endpoint': endpoint,
            'duration_ms': 0
        }
        self.logger.info(
            f"API Request: {method} {endpoint} - Payload: {json.dumps(payload or {})}",
            extra=extra
        )
    
    def log_api_response(self, endpoint: str, status_code: int, request_id: str,
                        response_data: dict = None, duration_ms: float = 0):
        """Log API response"""
        extra = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'name': 'NotificationSystem',
            'request_id': request_id,
            'user_id': 'system',
            'endpoint': endpoint,
            'duration_ms': duration_ms
        }
        self.logger.info(
            f"API Response: {endpoint} - Status: {status_code} - Duration: {duration_ms}ms",
            extra=extra
        )
    
    def log_error(self, error: str, request_id: str, endpoint: str = None, 
                 user_id: str = None, error_type: str = "Exception"):
        """Log errors"""
        extra = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'ERROR',
            'name': 'NotificationSystem',
            'request_id': request_id,
            'user_id': user_id or 'system',
            'endpoint': endpoint or 'unknown',
            'duration_ms': 0
        }
        self.logger.error(
            f"{error_type}: {error}",
            extra=extra
        )
    
    def log_database_query(self, query: str, execution_time_ms: float, 
                          request_id: str, user_id: str = None):
        """Log database queries"""
        extra = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'DEBUG',
            'name': 'NotificationSystem',
            'request_id': request_id,
            'user_id': user_id or 'system',
            'endpoint': 'database',
            'duration_ms': execution_time_ms
        }
        self.logger.debug(
            f"DB Query: {query} - Execution Time: {execution_time_ms}ms",
            extra=extra
        )
    
    def log_notification_action(self, action: str, notification_id: str, 
                               user_id: str, request_id: str, details: dict = None):
        """Log notification-specific actions"""
        extra = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'name': 'NotificationSystem',
            'request_id': request_id,
            'user_id': user_id,
            'endpoint': f'notification/{action}',
            'duration_ms': 0
        }
        self.logger.info(
            f"Notification Action: {action} - NotificationID: {notification_id} - Details: {json.dumps(details or {})}",
            extra=extra
        )
    
    def log_bulk_operation(self, operation: str, total_count: int, 
                          successful: int, failed: int, request_id: str):
        """Log bulk operations like 'notify all'"""
        extra = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': 'INFO',
            'name': 'NotificationSystem',
            'request_id': request_id,
            'user_id': 'system',
            'endpoint': f'bulk/{operation}',
            'duration_ms': 0
        }
        self.logger.info(
            f"Bulk Operation: {operation} - Total: {total_count}, Successful: {successful}, Failed: {failed}",
            extra=extra
        )


# Global logger instance
logger = NotificationLogger()
