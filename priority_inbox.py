"""
Priority Inbox Implementation
Implements efficient priority notification retrieval and maintenance
"""

from datetime import datetime
from typing import List, Dict
import heapq


class PriorityNotification:
    """Represents a notification with priority score"""
    
    def __init__(self, notification_id: str, message: str, notification_type: str,
                 created_at: datetime, priority_weight: int):
        self.notification_id = notification_id
        self.message = message
        self.notification_type = notification_type
        self.created_at = created_at
        self.priority_weight = priority_weight
        
        # Calculate priority score: weight (0-3) and recency (inverse of age in seconds)
        time_diff = (datetime.utcnow() - created_at).total_seconds()
        # Normalize recency score (0-1 scale, newer = higher)
        recency_score = max(0, 1 - (time_diff / (7 * 24 * 3600)))  # 7 days normalize
        
        # Combined priority score: 70% weight, 30% recency
        self.priority_score = (self.priority_weight / 3 * 0.7) + (recency_score * 0.3)
    
    def __lt__(self, other):
        """Less than operator for heap (min heap, so we negate for max heap)"""
        if self.priority_score != other.priority_score:
            return self.priority_score > other.priority_score  # Reverse for max heap
        return self.created_at > other.created_at
    
    def to_dict(self) -> Dict:
        return {
            'notification_id': self.notification_id,
            'message': self.message,
            'type': self.notification_type,
            'created_at': self.created_at.isoformat(),
            'priority_weight': self.priority_weight,
            'priority_score': round(self.priority_score, 3)
        }


class PriorityInbox:
    """Manages priority inbox for efficient top-N retrieval"""
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.heap: List[PriorityNotification] = []
        self.notification_set = set()  # For O(1) existence check
    
    def add_notification(self, notification: PriorityNotification):
        """Add a notification to the priority inbox"""
        if notification.notification_id in self.notification_set:
            return  # Already exists
        
        heapq.heappush(self.heap, notification)
        self.notification_set.add(notification.notification_id)
        
        # Maintain max size by removing lowest priority item
        if len(self.heap) > self.max_size:
            removed = heapq.heappop(self.heap)
            self.notification_set.remove(removed.notification_id)
    
    def get_top_notifications(self, limit: int = None) -> List[Dict]:
        """Get top notifications sorted by priority"""
        limit = limit or self.max_size
        
        # Sort heap and return top N
        sorted_heap = sorted(self.heap, reverse=True)[:limit]
        return [notif.to_dict() for notif in sorted_heap]
    
    def size(self) -> int:
        """Get current size of inbox"""
        return len(self.heap)
    
    def is_full(self) -> bool:
        """Check if inbox is at max capacity"""
        return len(self.heap) >= self.max_size


class PriorityInboxManager:
    """Manages multiple priority inboxes for different students"""
    
    def __init__(self):
        self.inboxes: Dict[str, PriorityInbox] = {}
    
    def get_or_create_inbox(self, student_id: str, max_size: int = 10) -> PriorityInbox:
        """Get or create a priority inbox for a student"""
        if student_id not in self.inboxes:
            self.inboxes[student_id] = PriorityInbox(max_size)
        return self.inboxes[student_id]
    
    def add_notification(self, student_id: str, notification: PriorityNotification, max_size: int = 10):
        """Add notification to a student's inbox"""
        inbox = self.get_or_create_inbox(student_id, max_size)
        inbox.add_notification(notification)
    
    def get_top_notifications(self, student_id: str, limit: int = None) -> List[Dict]:
        """Get top notifications for a student"""
        if student_id not in self.inboxes:
            return []
        
        inbox = self.inboxes[student_id]
        return inbox.get_top_notifications(limit)
    
    def clear_inbox(self, student_id: str):
        """Clear a student's priority inbox"""
        if student_id in self.inboxes:
            del self.inboxes[student_id]


# Global inbox manager instance
priority_inbox_manager = PriorityInboxManager()
