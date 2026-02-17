#!/bin/bash
# ==============================================================================
# HealthGuard Ops - Fix and Restart Script
# ==============================================================================
# This script fixes common issues and restarts all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     HealthGuard Ops - Fix and Restart Script              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Stop all services
echo -e "${YELLOW}⏹️  Step 1: Stopping all services...${NC}"
docker-compose down

# Step 2: Remove volumes to force database reinitialization
echo -e "${YELLOW}🗑️  Step 2: Removing volumes (forces database reinitialization)...${NC}"
docker volume rm healthguard-ops_postgres-data 2>/dev/null || echo "Volume already removed or doesn't exist"
docker volume rm healthguard-ops_grafana-data 2>/dev/null || echo "Grafana volume already removed or doesn't exist"

# Step 3: Rebuild and start all services
echo -e "${YELLOW}🔨 Step 3: Building and starting all services...${NC}"
docker-compose up -d --build

# Step 4: Wait for services to initialize
echo -e "${YELLOW}⏳ Step 4: Waiting 60 seconds for services to initialize...${NC}"
for i in {60..1}; do
    echo -ne "${BLUE}   $i seconds remaining...\r${NC}"
    sleep 1
done
echo ""

# Step 5: Verify database tables
echo -e "${YELLOW}🔍 Step 5: Verifying database initialization...${NC}"
echo -e "${BLUE}Tables in database:${NC}"
docker-compose exec -T database psql -U postgres -d incident_platform -c "\dt" | grep -E "alerts|incidents|employees|notifications" || {
    echo -e "${RED}❌ Database tables not found!${NC}"
    echo -e "${YELLOW}Running init script manually...${NC}"
    docker-compose exec -T database psql -U postgres -d incident_platform < init-scripts/01-init.sql
}

# Count employees
EMPLOYEE_COUNT=$(docker-compose exec -T database psql -U postgres -d incident_platform -t -c "SELECT COUNT(*) FROM employees;" | tr -d ' ')
echo -e "${GREEN}✅ Employees in database: $EMPLOYEE_COUNT${NC}"

# Step 6: Verify all services are healthy
echo ""
echo -e "${YELLOW}🏥 Step 6: Checking service health...${NC}"

services=("8001:Alert Ingestion" "8002:Incident Management" "8003:On-Call Service" "8004:Notification Service" "8080:Web UI")

all_healthy=true
for service in "${services[@]}"; do
    IFS=':' read -r port name <<< "$service"
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $name (port $port) is healthy${NC}"
    else
        echo -e "${RED}❌ $name (port $port) is not responding${NC}"
        all_healthy=false
    fi
done

# Step 7: Check Prometheus targets
echo ""
echo -e "${YELLOW}📊 Step 7: Checking Prometheus...${NC}"
if curl -f -s "http://localhost:9090/-/ready" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Prometheus is ready${NC}"

    # Check if targets are up
    sleep 5
    echo -e "${BLUE}Prometheus targets:${NC}"
    curl -s "http://localhost:9090/api/v1/targets" | grep -o '"health":"[^"]*"' | sort -u || echo "Could not fetch targets"
else
    echo -e "${RED}❌ Prometheus is not ready${NC}"
    all_healthy=false
fi

# Step 8: Check Grafana
echo ""
echo -e "${YELLOW}📈 Step 8: Checking Grafana...${NC}"
if curl -f -s "http://localhost:3001/api/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Grafana is ready${NC}"
else
    echo -e "${RED}❌ Grafana is not ready${NC}"
    all_healthy=false
fi

# Step 9: Generate test alert
echo ""
echo -e "${YELLOW}🧪 Step 9: Generating test alert...${NC}"
response=$(curl -s -X POST http://localhost:8001/alerts/manual)
if echo "$response" | grep -q "alert_id"; then
    echo -e "${GREEN}✅ Test alert created successfully${NC}"
    echo "$response" | grep -o '"alert_id":"[^"]*"'
else
    echo -e "${RED}❌ Failed to create test alert${NC}"
    echo "Response: $response"
    echo ""
    echo -e "${YELLOW}Checking alert-ingestion logs:${NC}"
    docker-compose logs --tail=20 alert-ingestion
fi

# Step 10: Summary
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}║                 ✅ ALL SERVICES HEALTHY ✅                 ║${NC}"
else
    echo -e "${YELLOW}║           ⚠️  SOME SERVICES MAY HAVE ISSUES ⚠️            ║${NC}"
fi
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Access your services:${NC}"
echo -e "  • Web UI:        http://localhost:8080"
echo -e "  • Grafana:       http://localhost:3001 ${YELLOW}(admin/admin)${NC}"
echo -e "  • Prometheus:    http://localhost:9090"
echo -e "  • Alert API:     http://localhost:8001"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Configure Prometheus datasource in Grafana manually"
echo -e "  2. Import dashboards from monitoring/grafana-dashboards/"
echo -e "  3. Generate more test data: ${YELLOW}curl -X POST http://localhost:8001/alerts/manual${NC}"
echo -e "  4. Take screenshots for hackathon submission! 📸"
echo ""

exit 0
