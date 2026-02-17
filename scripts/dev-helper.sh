#!/bin/bash

# HealthGuard Ops - Developer Helper Script
# Quick commands for common operations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose not found! Please install Docker Compose."
    exit 1
fi

# Main menu
show_menu() {
    echo ""
    echo "╔════════════════════════════════════════════════════╗"
    echo "║      HealthGuard Ops - Developer Helper           ║"
    echo "╚════════════════════════════════════════════════════╝"
    echo ""
    echo "Quick Commands:"
    echo ""
    echo "  1)  Start all services"
    echo "  2)  Stop all services"
    echo "  3)  Restart all services"
    echo "  4)  View logs (all services)"
    echo "  5)  View status"
    echo "  6)  Check health (all services)"
    echo "  7)  Rebuild and restart"
    echo "  8)  Clean up (remove containers)"
    echo "  9)  Nuclear reset (clean everything)"
    echo "  10) Open Web UI in browser"
    echo ""
    echo "Service-Specific:"
    echo ""
    echo "  11) Restart web-ui"
    echo "  12) Restart alert-ingestion"
    echo "  13) Restart incident-management"
    echo "  14) Restart oncall-service"
    echo "  15) View web-ui logs"
    echo "  16) View database logs"
    echo ""
    echo "Database:"
    echo ""
    echo "  17) Connect to database"
    echo "  18) Backup database"
    echo "  19) Reset database"
    echo ""
    echo "Monitoring:"
    echo ""
    echo "  20) Open Prometheus"
    echo "  21) Open Grafana"
    echo "  22) Show resource usage"
    echo ""
    echo "  0) Exit"
    echo ""
    echo -n "Enter your choice: "
}

# Function implementations
start_all() {
    print_info "Starting all services..."
    docker-compose up -d
    print_success "All services started!"
    docker-compose ps
}

stop_all() {
    print_info "Stopping all services..."
    docker-compose stop
    print_success "All services stopped!"
}

restart_all() {
    print_info "Restarting all services..."
    docker-compose restart
    print_success "All services restarted!"
    docker-compose ps
}

view_logs() {
    print_info "Viewing logs (Ctrl+C to exit)..."
    docker-compose logs -f --tail=100
}

view_status() {
    print_info "Service Status:"
    docker-compose ps
    echo ""
    print_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

check_health() {
    print_info "Checking health endpoints..."
    echo ""

    check_endpoint() {
        local name=$1
        local url=$2
        if curl -sf "$url" > /dev/null 2>&1; then
            print_success "$name is healthy"
        else
            print_error "$name is unhealthy or not responding"
        fi
    }

    check_endpoint "Alert Ingestion (8001)" "http://localhost:8001/health"
    check_endpoint "Incident Management (8002)" "http://localhost:8002/health"
    check_endpoint "On-Call Service (8003)" "http://localhost:8003/health"
    check_endpoint "Web UI (8080)" "http://localhost:8080/health"
    check_endpoint "Prometheus (9090)" "http://localhost:9090/-/healthy"
    check_endpoint "Grafana (3001)" "http://localhost:3001/api/health"
}

rebuild_and_restart() {
    print_warning "This will rebuild all services. Continue? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Building all services..."
        docker-compose build
        print_info "Restarting services..."
        docker-compose up -d
        print_success "Rebuild complete!"
        docker-compose ps
    else
        print_info "Cancelled."
    fi
}

clean_up() {
    print_warning "This will remove all containers but keep data. Continue? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        docker-compose down
        print_success "Cleanup complete!"
    else
        print_info "Cancelled."
    fi
}

nuclear_reset() {
    print_error "⚠️  WARNING: This will delete EVERYTHING (containers, images, volumes, data)!"
    print_warning "Are you absolutely sure? Type 'YES' to confirm:"
    read -r response
    if [[ "$response" == "YES" ]]; then
        print_info "Performing nuclear reset..."
        docker-compose down -v
        docker system prune -a -f
        docker volume prune -f
        print_success "Nuclear reset complete! Run option 7 to rebuild."
    else
        print_info "Cancelled. (You must type 'YES' in all caps)"
    fi
}

open_web_ui() {
    print_info "Opening Web UI in browser..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8080
    elif command -v open &> /dev/null; then
        open http://localhost:8080
    else
        print_info "Please open http://localhost:8080 in your browser"
    fi
}

restart_service() {
    local service=$1
    print_info "Restarting $service..."
    docker-compose restart "$service"
    print_success "$service restarted!"
    docker-compose logs --tail=20 "$service"
}

view_service_logs() {
    local service=$1
    print_info "Viewing $service logs (Ctrl+C to exit)..."
    docker-compose logs -f --tail=100 "$service"
}

connect_database() {
    print_info "Connecting to database..."
    print_info "Commands: \\l (list databases), \\dt (list tables), \\q (quit)"
    docker exec -it healthguard-postgres psql -U postgres -d incident_platform
}

backup_database() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    print_info "Backing up database to $backup_file..."
    docker exec healthguard-postgres pg_dump -U postgres incident_platform > "$backup_file"
    print_success "Database backed up to $backup_file"
}

reset_database() {
    print_warning "This will DELETE all database data! Continue? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Resetting database..."
        docker-compose down -v
        docker-compose up -d database
        sleep 5
        docker-compose up -d
        print_success "Database reset complete!"
    else
        print_info "Cancelled."
    fi
}

open_prometheus() {
    print_info "Opening Prometheus..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:9090
    elif command -v open &> /dev/null; then
        open http://localhost:9090
    else
        print_info "Please open http://localhost:9090 in your browser"
    fi
}

open_grafana() {
    print_info "Opening Grafana (admin/admin)..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:3001
    elif command -v open &> /dev/null; then
        open http://localhost:3001
    else
        print_info "Please open http://localhost:3001 in your browser"
    fi
}

show_resource_usage() {
    print_info "Resource Usage (updating every 2 seconds, Ctrl+C to exit)..."
    docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Main loop
while true; do
    show_menu
    read -r choice

    case $choice in
        1) start_all ;;
        2) stop_all ;;
        3) restart_all ;;
        4) view_logs ;;
        5) view_status ;;
        6) check_health ;;
        7) rebuild_and_restart ;;
        8) clean_up ;;
        9) nuclear_reset ;;
        10) open_web_ui ;;
        11) restart_service "web-ui" ;;
        12) restart_service "alert-ingestion" ;;
        13) restart_service "incident-management" ;;
        14) restart_service "oncall-service" ;;
        15) view_service_logs "web-ui" ;;
        16) view_service_logs "database" ;;
        17) connect_database ;;
        18) backup_database ;;
        19) reset_database ;;
        20) open_prometheus ;;
        21) open_grafana ;;
        22) show_resource_usage ;;
        0)
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice. Please try again."
            ;;
    esac

    echo ""
    echo -n "Press Enter to continue..."
    read -r
done
