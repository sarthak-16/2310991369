"""
Stage 6: Priority Notifications Implementation
Fetches top 10 notifications from external API with priority ordering
"""

import requests
import json
from datetime import datetime
from typing import List, Dict
from priority_inbox import PriorityNotification, priority_inbox_manager


class NotificationAPIClient:
    """Client for fetching notifications from external API"""
    
    def __init__(self, api_url: str = "http://20.207.122.201/evaluation-service/notifications"):
        self.api_url = api_url
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer YOUR_TOKEN_HERE'  # Add your actual token
        }
    
    def fetch_all_notifications(self, student_id: str = None) -> Dict:
        """Fetch all notifications from API"""
        try:
            response = requests.get(
                self.api_url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching notifications: {str(e)}")
            return {'notifications': []}
    
    def fetch_paginated_notifications(self, page: int = 1, limit: int = 100) -> Dict:
        """Fetch notifications with pagination"""
        try:
            params = {'page': page, 'limit': limit}
            response = requests.get(
                self.api_url,
                headers=self.headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching paginated notifications: {str(e)}")
            return {'notifications': []}


class PriorityNotificationProcessor:
    """Processes notifications and maintains priority inbox"""
    
    # Priority weights for notification types
    PRIORITY_WEIGHTS = {
        'Placement': 3,
        'Result': 2,
        'Event': 1
    }
    
    def __init__(self, api_client: NotificationAPIClient = None):
        self.api_client = api_client or NotificationAPIClient()
        self.manager = priority_inbox_manager
    
    def process_notification(self, notification_data: Dict) -> PriorityNotification:
        """Convert API notification to PriorityNotification"""
        # Parse timestamp
        try:
            created_at = datetime.strptime(notification_data['Timestamp'], '%Y-%m-%d %H:%M:%S')
        except (ValueError, KeyError):
            created_at = datetime.utcnow()
        
        # Get priority weight
        notification_type = notification_data.get('Type', 'Event')
        priority_weight = self.PRIORITY_WEIGHTS.get(notification_type, 1)
        
        return PriorityNotification(
            notification_id=notification_data.get('ID', ''),
            message=notification_data.get('Message', ''),
            notification_type=notification_type,
            created_at=created_at,
            priority_weight=priority_weight
        )
    
    def get_top_notifications(self, student_id: str, limit: int = 10) -> List[Dict]:
        """
        Fetch and return top N notifications for a student
        
        Algorithm:
        1. Fetch all notifications from API
        2. Convert to PriorityNotification objects
        3. Use heap to maintain top N efficiently
        4. Return sorted by priority
        """
        # Note: In production, you'd fetch only this student's notifications
        # For demo purposes, we're fetching all and filtering
        
        # Step 1: Fetch notifications from API
        api_response = self.api_client.fetch_all_notifications()
        notifications = api_response.get('notifications', [])
        
        # Step 2: Process all notifications
        priority_notifs = []
        for notif_data in notifications:
            try:
                priority_notif = self.process_notification(notif_data)
                priority_notifs.append(priority_notif)
            except Exception as e:
                print(f"Error processing notification: {str(e)}")
                continue
        
        # Step 3: Use heap to get top N
        if len(priority_notifs) <= limit:
            top_notifications = sorted(priority_notifs, reverse=True)[:limit]
        else:
            # Use heapq.nlargest for efficiency
            import heapq
            top_notifications = heapq.nlargest(limit, priority_notifs)
        
        # Step 4: Convert to dictionaries
        result = [notif.to_dict() for notif in top_notifications]
        
        # Cache in priority inbox for faster future access
        for notif in top_notifications:
            self.manager.add_notification(student_id, notif, limit)
        
        return result
    
    def get_top_notifications_by_type(self, student_id: str, notification_type: str, 
                                    limit: int = 10) -> List[Dict]:
        """Get top notifications of a specific type"""
        api_response = self.api_client.fetch_all_notifications()
        notifications = api_response.get('notifications', [])
        
        # Filter by type
        filtered_notifs = [
            n for n in notifications 
            if n.get('Type') == notification_type
        ]
        
        # Process and sort
        priority_notifs = []
        for notif_data in filtered_notifs:
            try:
                priority_notif = self.process_notification(notif_data)
                priority_notifs.append(priority_notif)
            except Exception as e:
                print(f"Error processing notification: {str(e)}")
                continue
        
        # Get top N
        import heapq
        top_notifications = heapq.nlargest(limit, priority_notifs)
        
        return [notif.to_dict() for notif in top_notifications]
    
    def maintain_top_n_efficiently(self, student_id: str, new_notification: Dict, 
                                  max_size: int = 10) -> List[Dict]:
        """
        Maintain top N notifications efficiently
        
        When new notifications arrive:
        1. Convert to PriorityNotification
        2. Add to heap
        3. If size > max, pop lowest priority
        4. Return current top N
        """
        try:
            # Convert new notification
            priority_notif = self.process_notification(new_notification)
            
            # Add to inbox
            self.manager.add_notification(student_id, priority_notif, max_size)
            
            # Return current top N
            return self.manager.get_top_notifications(student_id, max_size)
        
        except Exception as e:
            print(f"Error maintaining top N: {str(e)}")
            return []


def demo_stage_6():
    """Demonstration of Stage 6 implementation"""
    print("=" * 80)
    print("STAGE 6: PRIORITY NOTIFICATIONS")
    print("=" * 80)
    
    processor = PriorityNotificationProcessor()
    
    # Simulated student ID
    student_id = "student_001"
    
    # Fetch and display top 10 notifications
    print("\n1. Fetching top 10 notifications...")
    top_notifications = processor.get_top_notifications(student_id, limit=10)
    
    print(f"\nTop 10 Notifications for {student_id}:")
    print(json.dumps(top_notifications, indent=2))
    
    # Display by type
    print("\n2. Fetching top Placement notifications...")
    placement_notifs = processor.get_top_notifications_by_type(
        student_id, 'Placement', limit=5
    )
    print(f"\nTop Placement Notifications:")
    print(json.dumps(placement_notifs, indent=2))
    
    # Demonstrate efficiency metrics
    print("\n3. Priority Inbox Statistics:")
    inbox = processor.manager.get_or_create_inbox(student_id, max_size=10)
    print(f"Current inbox size: {inbox.size()}")
    print(f"Inbox capacity: {inbox.max_size}")
    print(f"Inbox full: {inbox.is_full()}")
    
    # Show how new notifications maintain efficiency
    print("\n4. Adding new notification and maintaining top N...")
    new_notification = {
        'ID': 'new-notif-001',
        'Type': 'Placement',
        'Message': 'TechCorp hiring now!',
        'Timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    updated_top = processor.maintain_top_n_efficiently(student_id, new_notification, max_size=10)
    print(f"\nUpdated top 10 (after adding new Placement notification):")
    for i, notif in enumerate(updated_top[:5], 1):
        print(f"  {i}. {notif['type']}: {notif['message']} (Priority: {notif['priority_score']})")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    demo_stage_6()
