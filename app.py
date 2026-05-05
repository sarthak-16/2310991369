"""
Main Flask Application for Campus Notification System
Implements REST API endpoints for notification management
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import uuid
import time
from models import db, Student, Notification, NotificationPreference, BulkNotificationJob, NotificationType
from logger_middleware import logger
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'sqlite:///./campus_notifications.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_SORT_KEYS'] = False

# Initialize extensions
db.init_app(app)
CORS(app)

# Request ID middleware
@app.before_request
def add_request_id():
    """Add request ID to all requests"""
    request.request_id = str(uuid.uuid4())
    request.start_time = time.time()


@app.after_request
def log_response(response):
    """Log API response"""
    duration_ms = (time.time() - request.start_time) * 1000
    logger.log_api_response(
        endpoint=request.path,
        status_code=response.status_code,
        request_id=request.request_id,
        duration_ms=duration_ms
    )
    return response


# ============ API ENDPOINTS ============

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """
    Get notifications for a student
    Query parameters: student_id, limit, page, notification_type
    """
    try:
        student_id = request.args.get('student_id')
        limit = int(request.args.get('limit', 20))
        page = int(request.args.get('page', 1))
        notification_type = request.args.get('notification_type')  # Optional filter
        
        logger.log_api_request('GET', '/api/notifications', request.request_id,
                             user_id=student_id, payload={'limit': limit, 'page': page})
        
        if not student_id:
            return jsonify({'error': 'student_id is required'}), 400
        
        # Build query
        query = Notification.query.filter_by(student_id=student_id)
        
        if notification_type:
            query = query.filter_by(notification_type=notification_type)
        
        # Optimize with proper sorting and pagination
        query = query.order_by(Notification.created_at.desc())
        
        total_count = query.count()
        notifications = query.offset((page - 1) * limit).limit(limit).all()
        
        logger.log_notification_action('fetch', 'multiple', student_id, request.request_id,
                                      {'total': total_count, 'returned': len(notifications)})
        
        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'total': total_count,
            'page': page,
            'limit': limit,
            'pages': (total_count + limit - 1) // limit
        }), 200
    
    except Exception as e:
        logger.log_error(str(e), request.request_id, '/api/notifications', 
                        error_type='GET_NOTIFICATIONS_ERROR')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/<notification_id>', methods=['GET'])
def get_notification(notification_id):
    """Get a specific notification"""
    try:
        logger.log_api_request('GET', f'/api/notifications/{notification_id}', request.request_id)
        
        notification = Notification.query.filter_by(id=notification_id).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        return jsonify(notification.to_dict()), 200
    
    except Exception as e:
        logger.log_error(str(e), request.request_id, f'/api/notifications/{notification_id}')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications', methods=['POST'])
def create_notification():
    """Create a new notification"""
    try:
        data = request.get_json()
        logger.log_api_request('POST', '/api/notifications', request.request_id, 
                             user_id=data.get('student_id'), payload=data)
        
        # Validate required fields
        required_fields = ['student_id', 'notification_type', 'message']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Verify student exists
        student = Student.query.filter_by(id=data['student_id']).first()
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Set priority weight based on type
        priority_weights = {'Placement': 3, 'Result': 2, 'Event': 1}
        priority_weight = priority_weights.get(data['notification_type'], 1)
        
        notification = Notification(
            student_id=data['student_id'],
            notification_type=data['notification_type'],
            message=data['message'],
            priority_weight=priority_weight,
            is_read=False
        )
        
        db.session.add(notification)
        db.session.commit()
        
        logger.log_notification_action('create', notification.id, data['student_id'],
                                      request.request_id, {'type': data['notification_type']})
        
        return jsonify(notification.to_dict()), 201
    
    except Exception as e:
        db.session.rollback()
        logger.log_error(str(e), request.request_id, '/api/notifications',
                        error_type='CREATE_NOTIFICATION_ERROR')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/<notification_id>/read', methods=['PUT'])
def mark_as_read(notification_id):
    """Mark notification as read"""
    try:
        notification = Notification.query.filter_by(id=notification_id).first()
        
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404
        
        notification.is_read = True
        notification.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.log_notification_action('mark_read', notification_id, notification.student_id,
                                      request.request_id)
        
        return jsonify(notification.to_dict()), 200
    
    except Exception as e:
        db.session.rollback()
        logger.log_error(str(e), request.request_id, f'/api/notifications/{notification_id}/read')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/unread', methods=['GET'])
def get_unread_notifications():
    """Get unread notifications for a student - OPTIMIZED QUERY"""
    try:
        student_id = request.args.get('student_id')
        limit = int(request.args.get('limit', 20))
        page = int(request.args.get('page', 1))
        
        if not student_id:
            return jsonify({'error': 'student_id is required'}), 400
        
        # Optimized query with proper indexing
        # The query now only fetches needed columns and uses indexed columns
        query = Notification.query.filter(
            Notification.student_id == student_id,
            Notification.is_read == False  # Using boolean index
        ).order_by(Notification.created_at.desc())
        
        total_count = query.count()
        notifications = query.offset((page - 1) * limit).limit(limit).all()
        
        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'total': total_count,
            'unread_count': total_count
        }), 200
    
    except Exception as e:
        logger.log_error(str(e), request.request_id, '/api/notifications/unread')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/priority', methods=['GET'])
def get_priority_notifications():
    """Get top N priority notifications for a student"""
    try:
        student_id = request.args.get('student_id')
        limit = int(request.args.get('limit', 10))
        
        if not student_id:
            return jsonify({'error': 'student_id is required'}), 400
        
        # Query optimized for priority ordering: weight DESC, created_at DESC
        notifications = Notification.query.filter_by(student_id=student_id)\
            .order_by(
                Notification.priority_weight.desc(),
                Notification.created_at.desc()
            )\
            .limit(limit)\
            .all()
        
        logger.log_notification_action('fetch_priority', 'multiple', student_id,
                                      request.request_id, {'limit': limit})
        
        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'count': len(notifications),
            'limit': limit
        }), 200
    
    except Exception as e:
        logger.log_error(str(e), request.request_id, '/api/notifications/priority')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/by-type', methods=['GET'])
def get_notifications_by_type():
    """Get notifications filtered by type in last N days"""
    try:
        student_id = request.args.get('student_id')
        notification_type = request.args.get('notification_type')
        days = int(request.args.get('days', 7))
        
        if not student_id or not notification_type:
            return jsonify({'error': 'student_id and notification_type are required'}), 400
        
        # Check if notification_type is valid
        valid_types = ['Placement', 'Result', 'Event']
        if notification_type not in valid_types:
            return jsonify({'error': f'Invalid notification_type. Must be one of: {valid_types}'}), 400
        
        # Query with date filter
        date_threshold = datetime.utcnow() - timedelta(days=days)
        
        notifications = Notification.query.filter(
            Notification.student_id == student_id,
            Notification.notification_type == notification_type,
            Notification.created_at >= date_threshold
        ).order_by(Notification.created_at.desc()).all()
        
        return jsonify({
            'notifications': [n.to_dict() for n in notifications],
            'count': len(notifications),
            'filter': {'type': notification_type, 'last_days': days}
        }), 200
    
    except Exception as e:
        logger.log_error(str(e), request.request_id, '/api/notifications/by-type')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/notifications/bulk-notify', methods=['POST'])
def bulk_notify():
    """Send notification to all students (with queue support)"""
    try:
        data = request.get_json()
        message = data.get('message')
        notification_type = data.get('notification_type', 'Event')
        
        if not message:
            return jsonify({'error': 'message is required'}), 400
        
        # Create a bulk job record
        job = BulkNotificationJob(
            job_type='notify_all',
            total_recipients=0,
            status='queued'
        )
        
        logger.log_api_request('POST', '/api/notifications/bulk-notify', request.request_id,
                             payload={'message': message[:50], 'type': notification_type})
        
        # Get all students
        students = Student.query.all()
        total_students = len(students)
        
        job.total_recipients = total_students
        db.session.add(job)
        db.session.commit()
        
        # Process notifications
        successful = 0
        failed = 0
        
        for student in students:
            try:
                priority_weights = {'Placement': 3, 'Result': 2, 'Event': 1}
                priority_weight = priority_weights.get(notification_type, 1)
                
                notification = Notification(
                    student_id=student.id,
                    notification_type=notification_type,
                    message=message,
                    priority_weight=priority_weight,
                    is_read=False
                )
                
                db.session.add(notification)
                db.session.commit()
                successful += 1
                job.successful_count = successful
                
            except Exception as e:
                failed += 1
                job.failed_count = failed
                logger.log_error(f'Bulk notify failed for student {student.id}: {str(e)}',
                               request.request_id, '/api/notifications/bulk-notify')
        
        job.status = 'completed'
        job.processed_count = successful + failed
        db.session.commit()
        
        logger.log_bulk_operation('notify_all', total_students, successful, failed, request.request_id)
        
        return jsonify({
            'job_id': job.id,
            'total': total_students,
            'successful': successful,
            'failed': failed,
            'status': 'completed'
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.log_error(str(e), request.request_id, '/api/notifications/bulk-notify',
                        error_type='BULK_NOTIFY_ERROR')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/api/students', methods=['POST'])
def create_student():
    """Create a new student"""
    try:
        data = request.get_json()
        
        # Check if student already exists
        if Student.query.filter_by(student_id=data['student_id']).first():
            return jsonify({'error': 'Student already exists'}), 409
        
        student = Student(
            student_id=data['student_id'],
            email=data['email'],
            name=data['name']
        )
        
        db.session.add(student)
        db.session.commit()
        
        # Create default preferences
        prefs = NotificationPreference(student_id=student.id)
        db.session.add(prefs)
        db.session.commit()
        
        return jsonify({'student_id': student.id}), 201
    
    except Exception as e:
        db.session.rollback()
        logger.log_error(str(e), request.request_id, '/api/students')
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.log_error(str(error), getattr(request, 'request_id', 'unknown'),
                    error_type='INTERNAL_SERVER_ERROR')
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        logger.log_api_request('INFO', 'Application Started', 'startup')
        print("Database tables created successfully!")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
