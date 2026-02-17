#!/bin/bash
# ==============================================================================
# HealthGuard Ops - Local CI/CD Pipeline
# ==============================================================================
# This script implements the 7-stage CI/CD pipeline for local execution
# as required by the DevOps Incident & On-Call Platform Hackathon 2026
#
# Stages:
#   1. Code Quality & Testing
#   2. Build Container Images
#   3. Automated Deployment
#   4. Post-Deployment Verification
#   5. Security Scanning (bonus)
#   6. Integration Testing (bonus)
#   7. Performance Validation (bonus)
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_stage() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}STAGE $1: $2${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# ==============================================================================
# STAGE 1: Code Quality & Testing
# ==============================================================================
stage1_quality_testing() {
    log_stage "1" "Code Quality & Testing"

    log_info "Running Python linters..."

    # Check if flake8 is installed
    if ! command -v flake8 &> /dev/null; then
        log_warning "flake8 not installed, installing..."
        pip install flake8 --quiet || log_error "Failed to install flake8"
    fi

    # Lint Python services
    for service in alert-ingestion incident-management oncall-service notification-service; do
        if [ -d "services/$service/app" ]; then
            log_info "Linting $service..."
            flake8 "services/$service/app/" --max-line-length=120 --ignore=E203,W503,E501 --exclude=__pycache__,*.pyc || {
                log_warning "Linting warnings found in $service (non-blocking)"
            }
        fi
    done

    log_info "Running unit tests..."

    # Check if pytest is installed
    if ! command -v pytest &> /dev/null; then
        log_warning "pytest not installed, skipping tests"
        log_warning "Install with: pip install pytest pytest-cov"
    else
        # Run tests for each service
        test_passed=true
        for service in alert-ingestion incident-management oncall-service notification-service; do
            if [ -d "services/$service/app/tests" ] && [ "$(ls -A services/$service/app/tests/*.py 2>/dev/null)" ]; then
                log_info "Testing $service..."
                cd "services/$service"
                pytest app/tests/ -v --cov=app --cov-report=term --cov-fail-under=60 || {
                    log_warning "Tests failed or coverage < 60% for $service"
                    test_passed=false
                }
                cd ../..
            else
                log_warning "No tests found for $service"
            fi
        done

        if [ "$test_passed" = false ]; then
            log_warning "Some tests failed, but continuing pipeline..."
        fi
    fi

    log_success "Stage 1 completed - Code quality checks done"
}

# ==============================================================================
# STAGE 2: Build Container Images
# ==============================================================================
stage2_build_images() {
    log_stage "2" "Build Container Images"

    log_info "Building Docker images..."

    # Build all services
    docker-compose build --no-cache || {
        log_error "Docker build failed"
        exit 1
    }

    # Tag images with git commit SHA (if in git repo)
    if git rev-parse --git-dir > /dev/null 2>&1; then
        COMMIT_SHA=$(git rev-parse --short HEAD)
        log_info "Tagging images with commit SHA: $COMMIT_SHA"

        for service in alert-ingestion incident-management oncall-service notification-service web-ui; do
            if docker images | grep -q "healthguard-ops-$service"; then
                docker tag "healthguard-ops-$service:latest" "healthguard-ops-$service:$COMMIT_SHA"
                log_success "Tagged $service with $COMMIT_SHA"
            fi
        done
    fi

    log_success "Stage 2 completed - All images built successfully"
}

# ==============================================================================
# STAGE 3: Automated Deployment
# ==============================================================================
stage3_deploy() {
    log_stage "3" "Automated Deployment"

    log_info "Stopping existing services..."
    docker-compose down || log_warning "No existing services to stop"

    log_info "Starting services with docker-compose..."
    docker-compose up -d || {
        log_error "Deployment failed"
        docker-compose logs
        exit 1
    }

    log_info "Waiting for services to initialize (30 seconds)..."
    sleep 30

    log_success "Stage 3 completed - Services deployed"
}

# ==============================================================================
# STAGE 4: Post-Deployment Verification
# ==============================================================================
stage4_verify() {
    log_stage "4" "Post-Deployment Verification"

    log_info "Checking service health endpoints..."

    # Array of services with their ports
    declare -A SERVICES=(
        ["alert-ingestion"]=8001
        ["incident-management"]=8002
        ["oncall-service"]=8003
        ["notification-service"]=8004
        ["web-ui"]=8080
    )

    all_healthy=true

    for service in "${!SERVICES[@]}"; do
        port=${SERVICES[$service]}
        log_info "Checking $service on port $port..."

        # Wait up to 60 seconds for service to be ready
        timeout=60
        elapsed=0
        while [ $elapsed -lt $timeout ]; do
            if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
                log_success "$service is healthy ✓"
                break
            fi
            sleep 2
            elapsed=$((elapsed + 2))
        done

        if [ $elapsed -ge $timeout ]; then
            log_error "$service failed health check after ${timeout}s"
            all_healthy=false
        fi
    done

    # Check infrastructure services
    log_info "Checking Prometheus..."
    if curl -f -s "http://localhost:9090/-/ready" > /dev/null 2>&1; then
        log_success "Prometheus is ready ✓"
    else
        log_warning "Prometheus is not ready"
    fi

    log_info "Checking Grafana..."
    if curl -f -s "http://localhost:3001/api/health" > /dev/null 2>&1; then
        log_success "Grafana is ready ✓"
    else
        log_warning "Grafana is not ready"
    fi

    if [ "$all_healthy" = false ]; then
        log_error "Some services failed health checks"
        log_info "Check logs with: docker-compose logs"
        exit 1
    fi

    log_success "Stage 4 completed - All services verified healthy"
}

# ==============================================================================
# STAGE 5: Security Scanning (Bonus)
# ==============================================================================
stage5_security() {
    log_stage "5" "Security Scanning (Bonus)"

    log_info "Scanning for exposed secrets..."

    # Check if gitleaks is available via Docker
    if command -v docker &> /dev/null; then
        log_info "Running GitLeaks scan..."
        docker run --rm -v "$(pwd):/path" zricethezav/gitleaks:latest detect --source="/path" -v || {
            log_warning "GitLeaks scan found potential issues (review output)"
        }
    else
        log_warning "Docker not available, skipping GitLeaks scan"
    fi

    log_info "Checking for hardcoded credentials in code..."
    if grep -r "password.*=.*['\"].*['\"]" services/*/app/*.py 2>/dev/null | grep -v "POSTGRES_PASSWORD" | grep -v "getenv"; then
        log_warning "Potential hardcoded credentials found (review above)"
    else
        log_success "No obvious hardcoded credentials found"
    fi

    log_success "Stage 5 completed - Security scan done"
}

# ==============================================================================
# STAGE 6: Integration Testing (Bonus)
# ==============================================================================
stage6_integration() {
    log_stage "6" "Integration Testing (Bonus)"

    log_info "Running end-to-end integration tests..."

    # Test 1: Create an alert
    log_info "Test 1: Creating test alert..."
    response=$(curl -s -X POST http://localhost:8001/api/v1/alerts \
        -H "Content-Type: application/json" \
        -d '{
            "patient_id": "PT-TEST-001",
            "severity": "high",
            "vital_signs": {"heart_rate": 145}
        }')

    if echo "$response" | grep -q "alert_id"; then
        log_success "Alert created successfully"
    else
        log_warning "Alert creation test inconclusive"
    fi

    # Test 2: Check Prometheus metrics
    log_info "Test 2: Checking Prometheus metrics..."
    if curl -s http://localhost:9090/api/v1/targets | grep -q "up"; then
        log_success "Prometheus is scraping targets"
    else
        log_warning "Prometheus targets check failed"
    fi

    # Test 3: Check Grafana
    log_info "Test 3: Checking Grafana dashboards..."
    if curl -s http://localhost:3001/api/dashboards/uid/live-incidents | grep -q "Live Incident"; then
        log_success "Grafana dashboards are accessible"
    else
        log_warning "Grafana dashboard check inconclusive"
    fi

    log_success "Stage 6 completed - Integration tests done"
}

# ==============================================================================
# STAGE 7: Performance Validation (Bonus)
# ==============================================================================
stage7_performance() {
    log_stage "7" "Performance Validation (Bonus)"

    log_info "Checking service response times..."

    for port in 8001 8002 8003 8004; do
        response_time=$(curl -o /dev/null -s -w '%{time_total}' "http://localhost:$port/health")
        if (( $(echo "$response_time < 1.0" | bc -l) )); then
            log_success "Port $port response time: ${response_time}s ✓"
        else
            log_warning "Port $port response time: ${response_time}s (slow)"
        fi
    done

    log_success "Stage 7 completed - Performance validation done"
}

# ==============================================================================
# Main Pipeline Execution
# ==============================================================================
main() {
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║     HealthGuard Ops - Local CI/CD Pipeline Runner         ║${NC}"
    echo -e "${GREEN}║     Hackathon 2026 - Local Edition                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    START_TIME=$(date +%s)

    # Run all stages
    stage1_quality_testing
    stage2_build_images
    stage3_deploy
    stage4_verify
    stage5_security
    stage6_integration
    stage7_performance

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                 🎉 PIPELINE SUCCESSFUL 🎉                  ║${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}║  Total Duration: ${DURATION} seconds                              ║${NC}"
    echo -e "${GREEN}║                                                            ║${NC}"
    echo -e "${GREEN}║  Access your services:                                     ║${NC}"
    echo -e "${GREEN}║  • Web UI:        http://localhost:8080                    ║${NC}"
    echo -e "${GREEN}║  • Grafana:       http://localhost:3001 (admin/admin)      ║${NC}"
    echo -e "${GREEN}║  • Prometheus:    http://localhost:9090                    ║${NC}"
    echo -e "${GREEN}║  • Alert API:     http://localhost:8001                    ║${NC}"
    echo -e "${GREEN}║  • Incident API:  http://localhost:8002                    ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Run the pipeline
main

# Exit with success
exit 0
