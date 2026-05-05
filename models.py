"""
Database Models for Campus Notification System
Defines the schema for Students, Notifications, and NotificationPreferences
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
import uuid

db = SQLAlchemy()


class NotificationType(Enum):
    """Enum for notification types"""
    PLACEMENT = "Placement"
    RESULT = "Result"
    EVENT = "Event"


class Student(db.Model):
    """Student model"""
    __tablename__ = 'students'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notifications = db.relationship('Notification', backref='student', lazy='dynamic', 
                                   cascade='all, delete-orphan')
    preferences = db.relationship('NotificationPreference', backref='student', 
                                 uselist=False, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Student {self.student_id}: {self.name}>'


class Notification(db.Model):
    """Notification model"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), 
                          nullable=False, index=True)
    notification_type = db.Column(db.String(50), nullable=False, index=True)  # Type: Placement, Result, Event
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Priority weight (higher = more important)
    # Placement: 3, Result: 2, Event: 1
    priority_weight = db.Column(db.Integer, default=1)
    
    # Indexes for common queries
    __table_args__ = (
        db.Index('idx_student_isread', 'student_id', 'is_read'),
        db.Index('idx_student_created', 'student_id', 'created_at'),
        db.Index('idx_notification_type_created', 'notification_type', 'created_at'),
        db.Index('idx_student_type_date', 'student_id', 'notification_type', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Notification {self.id}: {self.notification_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'type': self.notification_type,
            'message': self.message,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat(),
            'priority_weight': self.priority_weight
        }


class NotificationPreference(db.Model):
    """User notification preferences"""
    __tablename__ = 'notification_preferences'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), 
                          nullable=False, unique=True, index=True)
    email_notifications = db.Column(db.Boolean, default=True)
    push_notifications = db.Column(db.Boolean, default=True)
    in_app_notifications = db.Column(db.Boolean, default=True)
    priority_inbox_limit = db.Column(db.Integer, default=10)  # Top N notifications
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationPreference {self.student_id}>'


class NotificationReadStatus(db.Model):
    """Track read/unread status for efficient queries"""
    __tablename__ = 'notification_read_status'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notification_id = db.Column(db.String(36), db.ForeignKey('notifications.id'), 
                               nullable=False, unique=True, index=True)
    student_id = db.Column(db.String(36), db.ForeignKey('students.id'), 
                          nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)  # NULL if unread
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_student_read_status', 'student_id', 'read_at'),
    )


class BulkNotificationJob(db.Model):
    """Track bulk notification jobs for reliability"""
    __tablename__ = 'bulk_notification_jobs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_type = db.Column(db.String(50), nullable=False)  # 'notify_all', etc.
    total_recipients = db.Column(db.Integer, nullable=False)
    processed_count = db.Column(db.Integer, default=0)
    successful_count = db.Column(db.Integer, default=0)
    failed_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed, failed
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BulkNotificationJob {self.id}: {self.status}>'
