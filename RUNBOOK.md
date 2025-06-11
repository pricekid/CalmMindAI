# Dear Teddy - Operations Runbook

## Database Backup & Restore Operations

### Manual Database Restore from S3

#### Prerequisites
- AWS CLI configured with access to `dearteddy-backups` S3 bucket
- PostgreSQL client tools (`psql`, `pg_restore`)
- Access to production database credentials

#### Steps
1. **List Available Backups**
   ```bash
   aws s3 ls s3://dearteddy-backups/backups/ --region us-east-1
   ```

2. **Download Backup File**
   ```bash
   # Replace BACKUP_FILENAME with actual backup file
   aws s3 cp s3://dearteddy-backups/backups/BACKUP_FILENAME.sql.gz ./restore_backup.sql.gz
   gunzip restore_backup.sql.gz
   ```

3. **Stop Application (if needed)**
   ```bash
   # In Render dashboard, temporarily scale service to 0 instances
   # Or use Render CLI: render services scale --service-id SERVICE_ID --replicas 0
   ```

4. **Restore Database**
   ```bash
   # Set database connection
   export PGPASSWORD="your_db_password"
   
   # Restore from backup
   psql -h hostname -p port -U username -d database_name -f restore_backup.sql
   ```

5. **Restart Application**
   ```bash
   # Scale back to normal in Render dashboard
   # Or use CLI: render services scale --service-id SERVICE_ID --replicas 1
   ```

#### Emergency Contact
- Database restoration should complete within 15-30 minutes for typical backup sizes
- Monitor application logs after restoration to ensure proper startup

---

## Service Rollback Operations

### Roll Back to Previous Git Commit on Render

#### Method 1: Through Render Dashboard
1. Navigate to your service in Render dashboard
2. Go to "Deploys" tab
3. Find the previous successful deployment
4. Click "Redeploy" on the desired commit
5. Monitor deployment logs for successful rollback

#### Method 2: Git Rollback + Push
```bash
# Check recent commits
git log --oneline -10

# Reset to previous commit (replace COMMIT_HASH)
git reset --hard COMMIT_HASH

# Force push to trigger new deployment
git push origin main --force
```

#### Method 3: Render CLI Rollback
```bash
# List recent deployments
render deploys list --service SERVICE_ID

# Trigger redeploy of specific commit
render deploys create --service SERVICE_ID --commit COMMIT_HASH
```

---

## Log Monitoring & Debugging

### Tailing Logs via Render CLI

#### Install Render CLI
```bash
# Download and install
curl -fsSL https://cli.render.com/install | sh

# Authenticate
render auth login
```

#### Real-time Log Streaming
```bash
# Stream all service logs
render logs --service SERVICE_ID --tail

# Filter by log level
render logs --service SERVICE_ID --tail --filter "ERROR"
render logs --service SERVICE_ID --tail --filter "INFO"

# Historical logs (last 100 lines)
render logs --service SERVICE_ID --lines 100
```

#### Application-Specific Logs
```bash
# Database connection logs
render logs --service SERVICE_ID --tail --filter "database"

# Authentication logs  
render logs --service SERVICE_ID --tail --filter "login\|auth"

# Error tracking
render logs --service SERVICE_ID --tail --filter "ERROR\|Exception\|Traceback"
```

### Log Analysis Patterns

#### Common Issues to Monitor
- `Database connection failed` - Check DATABASE_URL
- `500 Internal Server Error` - Check application logs for Python exceptions
- `Memory usage` - Monitor for memory leaks
- `CSRF token` - Authentication flow issues

---

## Emergency Procedures

### Service Health Check
```bash
# Check service status
curl -I https://dear-teddy.onrender.com/

# Verify database connectivity
curl -s https://dear-teddy.onrender.com/health | grep "database"
```

### Quick Fixes

#### 1. Application Not Starting
```bash
# Check environment variables
render services env list --service SERVICE_ID

# Verify required secrets are set
# DATABASE_URL, SENDGRID_API_KEY, OPENAI_API_KEY, etc.
```

#### 2. Database Connection Issues
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT version();"

# Check database size and connections
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database()));"
```

#### 3. High Memory Usage
- Scale service temporarily to higher memory plan
- Check for memory leaks in recent deployments
- Consider rolling back to previous stable version

### Escalation Contacts
- **Infrastructure Issues**: Render Support
- **Application Bugs**: Development Team
- **Database Issues**: Database Administrator

---

## Maintenance Windows

### Scheduled Backup Verification
- **Frequency**: Daily at 02:00 UTC
- **Retention**: 30 days
- **Verification**: Weekly test restore to staging environment

### Service Updates
- **Deploy Schedule**: Business hours preferred (9 AM - 5 PM EST)
- **Rollback Plan**: Always have previous commit ready for quick rollback
- **Testing**: Verify core functionality after each deployment

---

## Contact Information

### Critical Service Information
- **Production URL**: https://dear-teddy.onrender.com
- **Backup Location**: S3 bucket `dearteddy-backups`
- **Service ID**: [Update with actual Render service ID]
- **Database**: PostgreSQL on Render

### Emergency Procedures
1. **Immediate Response**: Check service status and logs
2. **Assessment**: Determine if rollback is needed
3. **Action**: Execute rollback or restore procedures
4. **Verification**: Confirm service restoration
5. **Documentation**: Log incident and resolution steps