# Calm Journey Database Recovery and Authentication Fix Plan

## Executive Summary

This document outlines our investigation into data loss and authentication issues affecting the Calm Journey application. Key findings indicate:

1. **Data Loss Issue**: The application experienced significant data loss, with only 3 journal entries currently in the database despite evidence suggesting 16+ entries existed previously.

2. **Authentication Problems**: Both user and admin login systems are experiencing issues, with error logs showing "'NoneType' object has no attribute 'split'" during login attempts.

3. **Database Migration Impact**: A migration from integer IDs to UUID-based IDs appears to have contributed to data accessibility issues.

4. **Dashboard Data Discrepancy**: The admin dashboard shows synthetic data (20 entries over 7 days) rather than actual database values.

This report provides a detailed analysis of these issues and outlines a recovery plan.

## Detailed Investigation Findings

### 1. Database Structure and Configuration

The application uses PostgreSQL with SQLAlchemy as the ORM. Key configuration settings:

```python
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///calm_journey.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_timeout": 60,
    "pool_size": 10,
    "max_overflow": 20,
    "isolation_level": "READ COMMITTED",
    "connect_args": {
        "connect_timeout": 10
    }
}
```

### 2. Database Migration Evidence

A significant migration occurred that changed user IDs from integers to UUIDs:

```python
# Create user table with string ID
logger.info("Creating user table...")
cursor.execute("""
CREATE TABLE "user" (
    id VARCHAR PRIMARY KEY,
    username VARCHAR(64) UNIQUE,
    email VARCHAR(120) UNIQUE,
    password_hash VARCHAR(256),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    first_name VARCHAR(64),
    last_name VARCHAR(64),
    profile_image_url VARCHAR(256),
    notifications_enabled BOOLEAN DEFAULT TRUE,
    notification_time TIME DEFAULT '09:00:00',
```

This migration involved:
- Dropping all existing tables
- Creating new tables with string IDs instead of integers
- Attempting to migrate data to the new schema

### 3. Data Storage Mechanisms

The application uses a hybrid approach to data storage:

1. **PostgreSQL Database**: Primary storage for users, journal entries, and CBT recommendations
2. **JSON Files**: Backup/legacy storage with files like:
   - `data/journals.json`: Main journal entries collection
   - `data/journals/user_X_journals.json`: Per-user journal files
   - `data/users.json.bak`: Backup of user data with old integer IDs

### 4. Data Loss Timeline

The evidence suggests data loss occurred between April 30 and May 13:

- Last database activity from logs: April 30, 2025
- Current database files created: May 13, 2025
- Activity data shows 16 weekly journal entries that aren't in the database

### 5. Authentication Issues

Authentication problems include:
- Error logs showing "'NoneType' object has no attribute 'split'" during login attempts
- Multiple emergency login routes created, suggesting persistent authentication failures
- User session handling issues potentially related to the ID format change

## Root Cause Analysis

After careful analysis, we've identified several likely root causes:

1. **Schema Incompatibility**: The migration from integer IDs to UUID strings appears incomplete, with some parts of the codebase still expecting integer IDs.

2. **Data Migration Failure**: The `import_legacy_data.py` and `import_legacy_journals.py` scripts show attempts to migrate data, but they may have failed part-way through or encountered unhandled edge cases.

3. **ID Mapping Inconsistency**: The `id_mapping.json` file may have incorrect mappings between old integer IDs and new UUID strings.

4. **Authentication Integration Issues**: The Replit Auth integration (used for authentication) may have compatibility issues with the database schema changes.

5. **Connection Pool Configuration**: While the connection pool settings have been improved (`pool_recycle`, `pool_pre_ping`, etc.), earlier connection issues may have contributed to data corruption.

## Recovery Plan

### Phase 1: Initial Assessment and Backup

1. **Create Comprehensive Backups**:
   ```bash
   # Run our recovery script to create backups
   python restore_journals.py
   ```

2. **Database Schema Verification**:
   ```sql
   -- Verify current database schema
   SELECT table_name, column_name, data_type 
   FROM information_schema.columns 
   WHERE table_schema = 'public';
   ```

3. **Export Current Database Data**:
   ```bash
   # Export current database to SQL file
   pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
   ```

### Phase 2: Data Recovery Implementation

1. **Fix ID Mapping**:
   - Verify and correct the mapping between old integer IDs and new UUIDs
   - Update the `id_mapping.json` file

2. **Enhance and Run Recovery Script**:
   - Execute our comprehensive recovery script:
   ```bash
   python restore_journals.py
   ```

3. **Recover from JSON Files**:
   - Extract and deduplicate entries from all potential sources:
   ```python
   # This is implemented in restore_journals.py
   all_journals = []
   for file_path in journal_files:
       journals = extract_journals_from_file(file_path)
       all_journals.extend(journals)
   ```

4. **Handle Legacy Field Names**:
   - Convert from old to new field names:
   ```python
   # Map old fields to new schema
   analysis = entry.get('analysis', entry.get('gpt_response', entry.get('feedback', '')))
   reflection = entry.get('reflection', entry.get('user_reflection', ''))
   followup = entry.get('followup_insight', entry.get('followup', ''))
   
   new_entry.initial_insight = analysis
   new_entry.followup_insight = followup
   new_entry.user_reflection = reflection
   ```

### Phase 3: Authentication Issues Fix

1. **Debug Authentication Flow**:
   - Add detailed logging to Replit Auth integration
   - Trace login process to identify NoneType error sources

2. **Fix Session Handling**:
   - Update session handling to work with UUID-based user IDs:
   ```python
   # Ensure stable session behavior with different ID formats
   session.permanent = True
   session.update({
       'is_admin': True,
       'admin_id': admin.id
   })
   ```

3. **Update Admin Authentication**:
   - Fix admin authentication to properly handle string IDs

### Phase 4: Database Consistency Verification

1. **Data Integrity Check**:
   ```sql
   -- Verify foreign key relationships
   SELECT
       tc.table_schema, 
       tc.constraint_name, 
       tc.table_name, 
       kcu.column_name, 
       ccu.table_schema AS foreign_table_schema,
       ccu.table_name AS foreign_table_name,
       ccu.column_name AS foreign_column_name 
   FROM 
       information_schema.table_constraints AS tc 
       JOIN information_schema.key_column_usage AS kcu
         ON tc.constraint_name = kcu.constraint_name
       JOIN information_schema.constraint_column_usage AS ccu 
         ON ccu.constraint_name = tc.constraint_name
   WHERE constraint_type = 'FOREIGN KEY';
   ```

2. **Fix Dashboard Data Source**:
   - Update admin dashboard to show actual data instead of mock data
   - Remove hardcoded values from `admin_dashboard_patch.py`

3. **Validate ID Consistency**:
   - Ensure all tables use UUID string IDs consistently
   - Update any remaining code that expects integer IDs

### Phase 5: Long-term Fixes

1. **Improve Error Handling**:
   - Enhance error handling in database migration scripts
   - Add transaction rollback for failed operations

2. **Create Regular Backups**:
   - Implement automated database backups with retention policy
   - Store backups outside the application directory

3. **Monitoring Implementation**:
   - Add database query monitoring
   - Implement alerting for potential data integrity issues

4. **Documentation Update**:
   - Document database schema and relationships
   - Create data recovery procedures documentation

## Post-Recovery Verification

1. **Data Count Verification**:
   - Confirm journal entry counts match expected values
   - Verify user data is complete and accessible

2. **Authentication Testing**:
   - Test admin and user login functionality
   - Verify session persistence across page loads

3. **Dashboard Accuracy**:
   - Confirm admin dashboard shows accurate, non-synthetic data
   - Verify all charts and statistics reflect database reality

4. **Performance Check**:
   - Monitor database query performance
   - Check connection pool utilization

## Conclusion

The data loss and authentication issues appear to stem from a significant database migration that changed the ID format from integers to UUIDs. While portions of the migration succeeded, some data and functionality were compromised in the process.

Our recovery plan focuses on:
1. Rescuing any available journal data from all potential sources
2. Fixing the mapping between old and new ID formats
3. Addressing authentication issues related to the ID format change
4. Ensuring database consistency and dashboard accuracy

If these recovery efforts don't fully restore the missing data, we recommend contacting the Replit support team to determine if additional backups might be available through their platform's snapshot or version history systems.