# Quick Start Guide

## Project Setup (5 minutes)

### Step 1: Clone and Setup Environment

```bash
cd campus-notification-system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Database

SQLite is used for local file-based storage (no external database needed):

```bash
# Copy environment file
cp .env.example .env

# Database will be automatically created at ./campus_notifications.db
# No additional setup required!
```

### Step 3: Initialize Database

```bash
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.create_all()
>>> exit()

# Verify database file created
# On Windows:
dir campus_notifications.db
# On macOS/Linux:
ls -la campus_notifications.db
```

### Step 4: Run Application

```bash
# In development mode
export FLASK_ENV=development  # On Windows: set FLASK_ENV=development
python app.py

# Application will start on http://localhost:5000
```

## Testing the API

### 1. Create a Student

```bash
curl -X POST "http://localhost:5000/api/students" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1042,
    "email": "student@example.com",
    "name": "John Doe"
  }'

# Response:
# {"student_id": "550e8400-e29b-41d4-a716-446655440000"}
```

### 2. Create Notifications

```bash
STUDENT_ID="550e8400-e29b-41d4-a716-446655440000"

# Create Placement notification
curl -X POST "http://localhost:5000/api/notifications" \
  -H "Content-Type: application/json" \
  -d "{
    \"student_id\": \"$STUDENT_ID\",
    \"notification_type\": \"Placement\",
    \"message\": \"Microsoft is hiring!\"
  }"

# Create Result notification
curl -X POST "http://localhost:5000/api/notifications" \
  -H "Content-Type: application/json" \
  -d "{
    \"student_id\": \"$STUDENT_ID\",
    \"notification_type\": \"Result\",
    \"message\": \"Your exam results are out\"
  }"

# Create Event notification
curl -X POST "http://localhost:5000/api/notifications" \
  -H "Content-Type: application/json" \
  -d "{
    \"student_id\": \"$STUDENT_ID\",
    \"notification_type\": \"Event\",
    \"message\": \"Tech fest happening tomorrow\"
  }"
```

### 3. Get All Notifications

```bash
curl -X GET "http://localhost:5000/api/notifications?student_id=$STUDENT_ID&limit=20&page=1"

# Response:
# {
#   "notifications": [
#     {
#       "id": "notif-id",
#       "student_id": "student-id",
#       "type": "Placement",
#       "message": "...",
#       "is_read": false,
#       "created_at": "2026-05-05T10:30:45.123456",
#       "priority_weight": 3
#     }
#   ],
#   "total": 3,
#   "page": 1,
#   "limit": 20,
#   "pages": 1
# }
```

### 4. Get Priority Notifications

```bash
curl -X GET "http://localhost:5000/api/notifications/priority?student_id=$STUDENT_ID&limit=10"

# Returns top 10 notifications sorted by priority (Placement > Result > Event)
```

### 5. Get Unread Notifications

```bash
curl -X GET "http://localhost:5000/api/notifications/unread?student_id=$STUDENT_ID&limit=20"
```

### 6. Mark as Read

```bash
NOTIF_ID="notification-id-from-above"

curl -X PUT "http://localhost:5000/api/notifications/$NOTIF_ID/read" \
  -H "Content-Type: application/json"
```

### 7. Bulk Notify All Students

```bash
curl -X POST "http://localhost:5000/api/notifications/bulk-notify" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Placement season started!",
    "notification_type": "Placement"
  }'

# Response shows progress
```

## Running Stage 6 Demo

```bash
# Execute the Stage 6 priority notification processor
python stage_6_implementation.py

# Output:
# ================================================================================
# STAGE 6: PRIORITY NOTIFICATIONS
# ================================================================================
# 
# 1. Fetching top 10 notifications...
# 
# Top 10 Notifications:
# [...]
```

## Logs

Logs are stored in `logs/notification_system.log` in JSON format:

```json
{
  "timestamp": "2026-05-05T10:30:45.123456",
  "level": "INFO",
  "name": "NotificationSystem",
  "message": "API Request: GET /api/notifications/unread - Payload: {...}",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "student_001",
  "endpoint": "/api/notifications/unread",
  "duration_ms": 45.23
}
```

View logs:
```bash
tail -f logs/notification_system.log
# or
cat logs/notification_system.log | python -m json.tool
```

## Database Queries

Connect to database:
```bash
psql campus_notifications
```

Useful queries:
```sql
-- Check table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
FROM pg_tables
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT 
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Get query performance stats
SELECT 
  query,
  mean_time,
  calls,
  total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"

**Solution**: Make sure virtual environment is activated and dependencies are installed
```bash
source venv/bin/activate  # or venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "psycopg2.OperationalError: could not connect to server"

**Solution**: Check PostgreSQL is running and connection string is correct
```bash
# macOS
brew services start postgresql

# Windows
net start PostgreSQL13

# Linux
sudo service postgresql start

# Verify
psql -U postgres -c "SELECT version();"
```

### Issue: "relation notifications does not exist"

**Solution**: Initialize database tables
```bash
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

### Issue: "Permission denied" when creating logs directory

**Solution**: Change permissions
```bash
chmod 755 logs
# or
mkdir -p logs
```

## Performance Monitoring

### Monitor Query Performance

```python
# In app.py, enable query logging
app.config['SQLALCHEMY_ECHO'] = True

# Watch database queries in console output
```

### Check Cache Hit Rate (Redis)

```bash
redis-cli
> INFO stats
# Look for keyspace_hits and keyspace_misses
# Hit rate = hits / (hits + misses)
```

### Load Testing

```bash
# Install locust
pip install locust

# Create locustfile.py with load tests
# Run load test
locust -f locustfile.py -u 100 -r 10 --run-time 60s
```

## Next Steps

1. **Implement Frontend React App** (See Stage 7)
2. **Set up Redis for Caching** (See Stage 4)
3. **Configure Celery for Async Tasks** (See Stage 5)
4. **Add Authentication** (JWT tokens)
5. **Deploy to Production** (Docker + Kubernetes)

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/14/orm/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

## Support

For issues or questions, refer to:
- `README.md` - Project overview
- `STAGES_GUIDE.md` - Detailed implementation guide
- `logger_middleware.py` - Logging examples
- `app.py` - API implementation

---

**Happy coding! 🚀**
