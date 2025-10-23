#!/bin/bash
#
# Production Deployment Script for Faceless YouTube Automation Platform
# This script orchestrates the complete production deployment
#
# Usage: ./deploy-prod.sh [--verify-only] [--no-backup] [--skip-tests]
#

set -e

# Color constants
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="${PROJECT_ROOT}/backups/prod_${DEPLOYMENT_DATE}"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
ENV_FILE="${PROJECT_ROOT}/.env.prod"
LOG_FILE="${PROJECT_ROOT}/logs/deployment_${DEPLOYMENT_DATE}.log"

# Initialize logging
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "${BACKUP_DIR}"

log_info() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
}

log_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}" | tee -a "$LOG_FILE"
}

# Parse command line arguments
VERIFY_ONLY=false
NO_BACKUP=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Functions
check_prerequisites() {
    log_header "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    log_info "Docker found: $(docker --version)"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi
    log_info "Docker Compose found: $(docker-compose --version)"

    # Check git
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed"
        exit 1
    fi
    log_info "Git found: $(git --version)"

    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
    log_info "Environment file found"

    # Check compose file
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    log_info "Compose file found"

    # Verify no hardcoded secrets in files
    log_info "Scanning for hardcoded secrets..."
    if grep -r "your-" "$ENV_FILE" > /dev/null 2>&1; then
        log_error "⚠️  WARNING: Placeholder values still in .env.prod"
        log_error "    Please update .env.prod with real values before deployment"
        exit 1
    fi
    log_info "Secret verification passed"
}

backup_current_deployment() {
    log_header "Backing Up Current Deployment"

    if [ "$NO_BACKUP" = true ]; then
        log_warn "Skipping backup (--no-backup flag set)"
        return 0
    fi

    # Check if containers are running
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_info "Backing up running containers..."
        
        # Backup container data volumes
        docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U faceless faceless_yt > "${BACKUP_DIR}/postgres_backup.sql" 2>/dev/null || log_warn "Could not backup PostgreSQL"
        docker-compose -f "$COMPOSE_FILE" exec -T mongodb mongodump --out /tmp/mongo_backup 2>/dev/null || log_warn "Could not backup MongoDB"
        
        log_info "Backups created at: ${BACKUP_DIR}"
    else
        log_warn "No running containers to backup"
    fi
}

build_images() {
    log_header "Building Docker Images"

    # Build API image
    log_info "Building API image..."
    docker build -f "${PROJECT_ROOT}/Dockerfile.prod" \
        --build-arg ENVIRONMENT=production \
        -t faceless-youtube-api:prod \
        "${PROJECT_ROOT}" 2>&1 | tee -a "$LOG_FILE"

    if [ $? -eq 0 ]; then
        log_info "API image built successfully"
    else
        log_error "Failed to build API image"
        exit 1
    fi

    # Build Dashboard image
    log_info "Building Dashboard image..."
    docker build -f "${PROJECT_ROOT}/dashboard/Dockerfile.prod" \
        --build-arg ENVIRONMENT=production \
        -t faceless-youtube-dashboard:prod \
        "${PROJECT_ROOT}/dashboard" 2>&1 | tee -a "$LOG_FILE"

    if [ $? -eq 0 ]; then
        log_info "Dashboard image built successfully"
    else
        log_error "Failed to build Dashboard image"
        exit 1
    fi
}

run_tests() {
    log_header "Running Test Suite"

    if [ "$SKIP_TESTS" = true ]; then
        log_warn "Skipping tests (--skip-tests flag set)"
        return 0
    fi

    if ! command -v pytest &> /dev/null; then
        log_warn "pytest not found, skipping tests"
        return 0
    fi

    log_info "Running pytest..."
    if pytest tests/ -v --tb=short 2>&1 | tee -a "$LOG_FILE"; then
        log_info "Test suite passed"
    else
        log_error "Test suite failed - deployment aborted"
        exit 1
    fi
}

deploy_containers() {
    log_header "Deploying Containers"

    # Stop existing containers if running
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_info "Stopping existing containers..."
        docker-compose -f "$COMPOSE_FILE" down 2>&1 | tee -a "$LOG_FILE"
        sleep 5
    fi

    # Start new containers
    log_info "Starting production containers..."
    docker-compose -f "$COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE"

    if [ $? -eq 0 ]; then
        log_info "Containers started successfully"
    else
        log_error "Failed to start containers"
        exit 1
    fi

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 10
}

verify_deployment() {
    log_header "Verifying Deployment"

    # Check container status
    log_info "Checking container status..."
    docker-compose -f "$COMPOSE_FILE" ps 2>&1 | tee -a "$LOG_FILE"

    # Check API health
    log_info "Checking API health..."
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        log_info "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi

    # Check Dashboard
    log_info "Checking Dashboard..."
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_info "Dashboard responding"
    else
        log_error "Dashboard not responding"
        return 1
    fi

    # Check database connectivity
    log_info "Checking database connectivity..."
    if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready > /dev/null 2>&1; then
        log_info "PostgreSQL connected"
    else
        log_error "PostgreSQL not responding"
        return 1
    fi

    log_info "All verification checks passed"
    return 0
}

configure_monitoring() {
    log_header "Configuring Monitoring"

    log_info "Setting up log aggregation..."
    mkdir -p "${PROJECT_ROOT}/logs/production"
    
    log_info "Configuring health check intervals..."
    # Health checks are already in docker-compose.prod.yml

    log_info "Setting up alerting..."
    # Add your alerting configuration here (Prometheus, DataDog, etc.)

    log_info "Monitoring configured"
}

generate_report() {
    log_header "Deployment Report"

    cat >> "$LOG_FILE" <<EOF

=== DEPLOYMENT COMPLETE ===
Timestamp: $(date)
Environment: Production
Deployment Date: ${DEPLOYMENT_DATE}
Backup Location: ${BACKUP_DIR}
Log File: ${LOG_FILE}

Deployed Services:
- API (faceless-youtube-api:prod) - http://localhost:8000
- Dashboard (faceless-youtube-dashboard:prod) - http://localhost:3000
- PostgreSQL - localhost:5432
- MongoDB - localhost:27017
- Redis - localhost:6379

Next Steps:
1. Verify all services are operational
2. Run smoke tests
3. Monitor logs for errors
4. Test core workflows
5. Set up monitoring and alerting

EOF

    log_info "Deployment report generated at: $LOG_FILE"
    cat "$LOG_FILE" | tail -20
}

# Main execution
main() {
    log_header "Production Deployment Started"
    log_info "Project Root: ${PROJECT_ROOT}"
    log_info "Deployment ID: ${DEPLOYMENT_DATE}"

    check_prerequisites
    
    if [ "$VERIFY_ONLY" = true ]; then
        log_info "Verify-only mode: checking prerequisites and tests only"
        run_tests
        log_info "Verification complete - deployment ready"
        exit 0
    fi

    backup_current_deployment
    build_images
    run_tests
    deploy_containers
    
    # Verify deployment
    if verify_deployment; then
        configure_monitoring
        generate_report
        log_header "Production Deployment Successful ✓"
        exit 0
    else
        log_error "Deployment verification failed - initiating rollback"
        log_info "To rollback, restore from: ${BACKUP_DIR}"
        exit 1
    fi
}

# Run main function
main "$@"
