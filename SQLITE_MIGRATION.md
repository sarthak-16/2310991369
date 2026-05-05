# SQLite Migration Guide

## Summary of Changes

The campus notification system has been converted from PostgreSQL to SQLite for local file-based database storage. This eliminates the need for external database dependencies.

## What Changed

### 1. **dependencies** (requirements.txt)
**Removed:**
- `psycopg2-binary==2.9.7` (PostgreSQL driver)

**Kept:**
- All other dependencies remain the same
- SQLAlchemy still used for ORM (supports both PostgreSQL and SQLite)

### 2. **Database Configuration** (config.py)

#### Development Config
```python
# Before (PostgreSQL):
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:password@localhost:5432/campus_notifications'

# After (SQLite):
SQLALCHEMY_DATABASE_URI = 'sqlite:///./campus_notifications.db'
```

#### Connection Pooling
```python
# Before (PostgreSQL):
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'max_overflow': 20,
}

# After (SQLite):
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 1,
    'connect_args': {'timeout': 10},
}
```

#### Production Config
```python
# Before (PostgreSQL):
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,
    'pool_recycle': 1800,
    'pool_pre_ping': True,
    'max_overflow': 40,
}

# After (SQLite):
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 1,
    'connect_args': {'timeout': 15},  # Increased timeout for file I/O
}
```

### 3. **Environment Configuration** (.env.example)

```bash
# Before (PostgreSQL):
DATABASE_URL=postgresql://postgres:password@localhost:5432/campus_notifications

# After (SQLite):
DATABASE_URL=sqlite:///./campus_notifications.db
```

## Benefits

✅ **No External Database Installation**
- SQLite is built into Python
- No need to install or run a separate PostgreSQL server

✅ **Simpler Setup**
- Database file auto-created on first run
- Reduced configuration complexity
- Perfect for local development and prototyping

✅ **File-Based Storage**
- Database stored as `campus_notifications.db` in project root
- Easy to backup, version control (excluded by .gitignore), or share
- No network overhead

✅ **Reduced Dependencies**
- One fewer package to install and maintain
- Faster pip install process

## Limitations & Considerations

⚠️ **Concurrent Access**
- SQLite has row-level locking (single writer at a time)
- Suitable for development and small-scale deployments
- For high-concurrency production, consider PostgreSQL

⚠️ **File Persistence**
- Keep backup of `campus_notifications.db` file
- File-based means I/O is tied to filesystem performance

⚠️ **Scaling**
- SQLite works well up to ~100GB databases
- For 50K students with 5M notifications, should be fine (~100-200MB)

## Migration Path

### For Existing PostgreSQL Data
If you have existing PostgreSQL data to migrate:

```python
# Create Python script to export PostgreSQL and import to SQLite
from app import app, db
from models import Student, Notification

# 1. Configure app with old PostgreSQL connection
# 2. Query data from PostgreSQL
# 3. Switch to SQLite connection
# 4. Insert data into SQLite

# Example:
with app.app_context():
    db.create_all()  # Creates SQLite tables
    
    # Query from PostgreSQL (if configured)
    students = Student.query.all()
    
    # Insert into SQLite (automatic if using same ORM)
    db.session.add_all(students)
    db.session.commit()
```

## Setup Instructions

### Quick Start (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize database
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.create_all()
>>> exit()

# 3. Run application
python app.py

# Application starts at http://localhost:5000
```

### Verify Setup

```bash
# Check database file created
ls -la campus_notifications.db

# Or on Windows:
dir campus_notifications.db

# Output should show file size (initially small, grows with data)
```

## API Compatibility

❌ **No API changes**
- All endpoints work exactly the same
- Request/response formats unchanged
- Query parameters identical

## Performance Notes

| Operation | SQLite Performance |
|-----------|-------------------|
| Reads | Very fast (local file) |
| Writes | Slower than PostgreSQL (file I/O) |
| Bulk inserts (1000+) | May be slower without PostgreSQL optimization |
| Complex joins | Supported, but less optimized |

## Troubleshooting

### Database Locked Error
```
sqlite3.OperationalError: database is locked
```

**Solution:**
- Increase timeout: `connect_args: {'timeout': 30}`
- Reduce concurrent connections
- Use connection pooling

### Reset Database
```bash
# Delete database file (all data lost)
rm campus_notifications.db

# Recreate empty database
python
>>> from app import app, db
>>> with app.app_context():
>>>     db.create_all()
```

### Backup Database
```bash
# Copy database file
cp campus_notifications.db campus_notifications.backup.db

# Or with timestamp
cp campus_notifications.db campus_notifications.$(date +%Y%m%d_%H%M%S).db
```

## When to Switch Back to PostgreSQL

Consider switching to PostgreSQL if you need:

- High concurrent write operations (100+ writes/second)
- Advanced features (window functions, custom types, extensions)
- Replication and disaster recovery
- JSON data with complex queries
- Production deployment with multi-application access

## References

- [SQLAlchemy SQLite Documentation](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html)
- [SQLite Official Documentation](https://www.sqlite.org/docs.html)
- [QUICKSTART.md](./QUICKSTART.md) - Quick setup guide
- [README.md](./README.md) - Full documentation
