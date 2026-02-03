# ABFI Platform 1 - Comprehensive Audit Checklist

## Backend API Endpoints to Test

### Sentiment API (`/api/v1/sentiment`)
- [ ] GET `/api/v1/sentiment/index` - Get current lending sentiment index
- [ ] POST `/api/v1/sentiment/analyze` - Analyze document for sentiment
- [ ] GET `/api/v1/sentiment/history` - Get historical sentiment data

### Prices API (`/api/v1/prices`)
- [ ] GET `/api/v1/prices/index/{feedstock}` - Get feedstock price index
- [ ] GET `/api/v1/prices/latest` - Get latest prices for all feedstocks
- [ ] GET `/api/v1/prices/history` - Get price history

### Policy API (`/api/v1/policy`)
- [ ] GET `/api/v1/policy/tracker` - Get policy updates feed
- [ ] GET `/api/v1/policy/mandate-scenarios` - Get SAF mandate scenarios
- [ ] GET `/api/v1/policy/by-jurisdiction` - Get policies by jurisdiction

### Carbon API (`/api/v1/carbon`)
- [ ] POST `/api/v1/carbon/calculate` - Calculate carbon revenue
- [ ] GET `/api/v1/carbon/scenarios` - Get saved scenarios

### Counterparty API (`/api/v1/counterparty`)
- [ ] GET `/api/v1/counterparty/{id}/rating` - Get counterparty risk rating
- [ ] GET `/api/v1/counterparty/list` - List all counterparties

### Intelligence API (`/api/v1/intelligence`)
- [ ] GET `/api/v1/intelligence/latest` - Get latest intelligence data
- [ ] POST `/api/v1/intelligence/refresh` - Trigger data refresh

### System Endpoints
- [ ] GET `/` - Root endpoint
- [ ] GET `/health` - Health check
- [ ] GET `/api/v1/status` - API status

## Frontend Pages to Test

### Dashboard Pages
- [ ] Sentiment Dashboard (`/sentiment`)
  - [ ] Sentiment index chart loads
  - [ ] Fear components display
  - [ ] Lender scores display
  - [ ] Historical data loads
  
- [ ] Prices Dashboard (`/prices`)
  - [ ] Price charts load
  - [ ] Commodity selector works
  - [ ] Region selector works
  - [ ] Historical data loads
  
- [ ] Policy Dashboard (`/policy`)
  - [ ] Policy list loads
  - [ ] Jurisdiction filter works
  - [ ] Policy type filter works
  - [ ] Timeline displays correctly

### UI Components
- [ ] Layout/Navigation works
- [ ] Charts render correctly
- [ ] KPI cards display data
- [ ] Badges and status indicators work

## Database Issues to Check

### Schema Consistency
- [ ] SQLite schema matches PostgreSQL schema in schema.sql
- [ ] All tables have proper indexes
- [ ] Foreign key constraints are correct
- [ ] JSONB fields are properly handled in SQLite (as TEXT)

### Data Integrity
- [ ] UUID generation works correctly
- [ ] Timestamps are properly formatted
- [ ] Unique constraints are enforced
- [ ] Default values are set correctly

## Code Quality Issues

### Backend
- [ ] All imports are correct
- [ ] Environment variables are properly configured
- [ ] Error handling is implemented
- [ ] Database connections are properly managed
- [ ] CORS is configured correctly

### Frontend
- [ ] API client is properly configured
- [ ] Environment variables are set
- [ ] Error handling for API calls
- [ ] Loading states are implemented
- [ ] Responsive design works

## Deployment Issues

### Vercel Configuration
- [ ] API routes are properly configured
- [ ] Environment variables are set
- [ ] Build process completes successfully
- [ ] Dashboard deploys correctly

### Database
- [ ] Turso connection works in production
- [ ] Database initialization runs correctly
- [ ] Migrations are applied
- [ ] Data seeding works

## Performance Issues
- [ ] API response times are acceptable
- [ ] Database queries are optimized
- [ ] Frontend loads quickly
- [ ] Charts render without lag

## Security Issues
- [ ] CORS is properly configured
- [ ] API authentication (if needed)
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention
- [ ] XSS prevention in frontend
