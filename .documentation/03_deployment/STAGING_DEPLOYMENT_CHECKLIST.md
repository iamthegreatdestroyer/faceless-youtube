# Staging Deployment Validation Checklist

## Pre-Deployment

- [ ] .env.staging file exists with all required variables
- [ ] Docker and docker-compose installed
- [ ] Project builds successfully locally
- [ ] All tests pass locally (dev environment)
- [ ] Git repository clean (no uncommitted changes)

## Deployment

- [ ] Staging directory prepared at /opt/faceless-youtube-staging
- [ ] Project files copied to staging
- [ ] Docker images built successfully
- [ ] docker-compose.staging.yml brings up all services
- [ ] All containers running and healthy
- [ ] No error logs in container startup

## Health Checks

- [ ] API health endpoint responds (http://localhost:8000/health)
- [ ] Dashboard loads (http://localhost:3000)
- [ ] PostgreSQL connection successful
- [ ] MongoDB connection successful
- [ ] Redis connection successful

## Smoke Tests

- [ ] All smoke tests pass (tests/smoke/)
- [ ] API endpoints return correct status codes
- [ ] Database queries return results
- [ ] Authentication flow works
- [ ] Job creation works end-to-end

## Performance Validation

- [ ] List jobs endpoint: <0.5s average
- [ ] Statistics endpoint: <1.0s average
- [ ] Health check: <0.1s average
- [ ] Database queries: <0.2s average
- [ ] No performance regressions detected

## Security Validation

- [ ] API requires authentication where needed
- [ ] CORS properly configured
- [ ] No sensitive data in logs
- [ ] Database credentials not exposed
- [ ] All secrets stored in .env.staging (not in code)

## Monitoring

- [ ] Prometheus metrics accessible
- [ ] Log aggregation working
- [ ] Error tracking enabled
- [ ] Performance metrics collecting

## Documentation

- [ ] Deployment process documented
- [ ] How to access staging environment documented
- [ ] How to run tests in staging documented
- [ ] Troubleshooting guide created
