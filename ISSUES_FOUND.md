# ABFI Platform 1 - Issues Found and Fixes Needed

## Critical Issues

### 1. Database Initialization Not Called
**Location**: `app/main.py` and `api/index.py`
**Severity**: CRITICAL
**Description**: Database tables are never initialized on startup
**Impact**: Application will fail when trying to query non-existent tables
**Fix**: Add `db.init_database()` call in startup lifespan

### 2. Missing API Entry Point for Vercel
**Location**: `api/index.py`
**Severity**: CRITICAL
**Description**: Vercel serverless function not properly configured
**Impact**: API won't work in production deployment
**Fix**: Ensure `api/index.py` properly exports the FastAPI app

### 3. Dashboard API Client Missing Base URL
**Location**: `dashboard/src/api/client.ts`
**Severity**: CRITICAL
**Description**: API base URL not configured for production
**Impact**: Frontend can't connect to backend API
**Fix**: Add environment variable for API_BASE_URL

## High Priority Issues

### 4. TODO: Implement Missing Endpoints
**Locations**: Multiple files
- `app/api/v1/carbon.py` - Carbon calculation not implemented
- `app/api/v1/counterparty.py` - All endpoints return mock data
- `app/api/v1/policy.py` - Database queries not implemented
- `app/api/v1/prices.py` - Price data endpoints incomplete

**Severity**: HIGH
**Impact**: Core features don't work, only return placeholder data
**Fix**: Implement actual database queries and business logic

### 5. Database Schema Mismatch
**Location**: `app/db/schema.sql` vs `app/db/database.py`
**Severity**: HIGH
**Description**: PostgreSQL schema.sql doesn't match SQLite implementation in database.py
**Impact**: Confusion, potential data loss, migration issues
**Fix**: Align schemas or remove unused schema.sql file

### 6. Missing Environment Variables
**Location**: `app/core/config.py`
**Severity**: HIGH
**Description**: Many required env vars not documented or have no defaults
**Impact**: Application fails to start without proper configuration
**Fix**: Add `.env.example` file with all required variables

### 7. CORS Configuration
**Location**: `app/main.py`
**Severity**: HIGH
**Description**: CORS origins from settings but not validated
**Impact**: Frontend may be blocked from accessing API
**Fix**: Ensure CORS allows dashboard domain in production

## Medium Priority Issues

### 8. Scheduler Not Working in Serverless
**Location**: `app/services/scheduler.py`
**Severity**: MEDIUM
**Description**: APScheduler won't work in Vercel serverless environment
**Impact**: Data refresh jobs won't run automatically
**Fix**: Use external cron service or Vercel Cron Jobs

### 9. Missing Error Handling
**Location**: Multiple API endpoints
**Severity**: MEDIUM
**Description**: Many endpoints lack try/catch error handling
**Impact**: Unhandled exceptions will crash the API
**Fix**: Add proper error handling and return appropriate HTTP status codes

### 10. Frontend Loading States
**Location**: Dashboard pages
**Severity**: MEDIUM
**Description**: No loading indicators while fetching data
**Impact**: Poor user experience, appears broken
**Fix**: Add loading spinners/skeletons

### 11. No Input Validation
**Location**: API endpoints
**Severity**: MEDIUM
**Description**: Limited validation on request parameters
**Impact**: Invalid data could cause errors or security issues
**Fix**: Add Pydantic validation on all input models

## Low Priority Issues

### 12. Mock Data Still in Production Code
**Location**: All API files
**Severity**: LOW
**Description**: Fallback mock data mixed with real data logic
**Impact**: Confusion about what's real vs mock
**Fix**: Remove mock data or clearly separate dev/prod modes

### 13. Unused Imports
**Location**: Multiple files
**Severity**: LOW
**Description**: Many unused imports throughout codebase
**Impact**: Code bloat, slower startup
**Fix**: Run linter and remove unused imports

### 14. Missing Type Hints
**Location**: Some functions
**Severity**: LOW
**Description**: Inconsistent type annotations
**Impact**: Reduced code quality and IDE support
**Fix**: Add type hints to all functions

## Database Refactoring Needed

### 15. Consolidate Database Implementations
**Current State**: 
- `app/db/schema.sql` - PostgreSQL schema (not used)
- `app/db/database.py` - SQLite implementation (used)
- `app/db/models.py` - Pydantic models (not used with DB)

**Needed**:
- Use SQLAlchemy ORM for proper database abstraction
- Support both SQLite (dev) and PostgreSQL/Turso (prod)
- Implement proper migrations with Alembic

### 16. Add Database Indexes
**Location**: `app/db/database.py`
**Severity**: MEDIUM
**Description**: Missing indexes on frequently queried columns
**Impact**: Slow queries as data grows
**Fix**: Add indexes on date columns, foreign keys, and search fields

### 17. Implement Connection Pooling
**Location**: `app/db/database.py`
**Severity**: MEDIUM
**Description**: No connection pooling for database
**Impact**: Performance issues under load
**Fix**: Use SQLAlchemy connection pool or similar

## Deployment Issues

### 18. Vercel Configuration
**Files to check**:
- `vercel.json` - API routes configuration
- `dashboard/vercel.json` - Frontend deployment config
- Environment variables in Vercel dashboard

### 19. Build Process
**Location**: `requirements-vercel.txt` vs `requirements.txt`
**Issue**: Two different requirement files
**Fix**: Ensure all dependencies are in vercel requirements

### 20. Static File Serving
**Location**: Dashboard build output
**Issue**: Need to ensure Vite build output is properly served
**Fix**: Verify vercel.json routes configuration

## Testing Needed

### 21. API Endpoint Testing
- Test all GET endpoints return valid data
- Test all POST endpoints accept and process data
- Test error cases return proper status codes
- Test CORS headers are correct

### 22. Frontend Integration Testing
- Test all dashboard pages load
- Test charts render with data
- Test navigation works
- Test responsive design

### 23. Database Testing
- Test database initialization
- Test all queries work
- Test data insertion and retrieval
- Test Turso connection in production

## Priority Fix Order

1. **Phase 1 - Critical Fixes** (Must fix for deployment)
   - Initialize database on startup
   - Fix Vercel API entry point
   - Configure dashboard API client
   - Set up environment variables

2. **Phase 2 - Core Functionality** (Make features work)
   - Implement missing API endpoints
   - Fix database queries
   - Add error handling
   - Test all endpoints

3. **Phase 3 - Polish** (Improve UX)
   - Add loading states
   - Remove mock data
   - Fix CORS issues
   - Add input validation

4. **Phase 4 - Optimization** (Performance)
   - Add database indexes
   - Implement connection pooling
   - Optimize queries
   - Add caching
