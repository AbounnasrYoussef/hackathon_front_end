# HealthGuard Ops - Hospital Incident Management Platform

Real-time incident management system for hospital operations with automated alerting, on-call scheduling, and SRE metrics monitoring.

## 🚀 Quick Start

```bash
# 1. Start all services
sudo docker-compose up -d

# 2. Wait for initialization (30 seconds)
sleep 30

# 3. Access the platform
# Web UI: http://localhost:8080
# Grafana: http://localhost:3001 (admin/admin)
# Prometheus: http://localhost:9090
```

**Login Credentials:**
- Nurses: N01-N06 / password123
- Emergency Doctors: D01-D04 / password123
- Specialists: S01-S12 / password123

## 📦 Architecture

### Services (Port)
- **Web UI** (8080) - React frontend with real-time notifications
- **Alert Ingestion** (8001) - Generates and processes patient alerts
- **Incident Management** (8002) - Incident lifecycle and assignment
- **On-Call Service** (8003) - Staff scheduling and authentication
- **Notification Service** (8004) - WebSocket notifications

### Infrastructure
- **PostgreSQL** (5432) - Database with 24 employees, 8 patients, 33 alert types
- **RabbitMQ** (5672, 15672) - Message queue for alert processing
- **Prometheus** (9090) - Metrics collection from all services
- **Grafana** (3001) - Live dashboards (Incidents, SRE Performance)

## 🛠️ Development

### Rebuild Services
```bash
# Rebuild all services
sudo docker-compose build

# Rebuild specific service
sudo docker-compose build web-ui
```

### View Logs
```bash
# All services
sudo docker-compose logs -f

# Specific service
sudo docker logs incident-management -f
```

### Database Access
```bash
# Connect to database
sudo docker exec -it healthguard-postgres psql -U postgres -d incident_platform

# Run SQL file
sudo docker exec -i healthguard-postgres psql -U postgres -d incident_platform < shared/schema.sql
```

### Generate Test Alerts
```bash
# Manual alert
curl -X POST http://localhost:8001/alerts/manual

# Multiple alerts
for i in {1..10}; do curl -X POST http://localhost:8001/alerts/manual; sleep 2; done
```

## 📊 Monitoring

### Prometheus Metrics
All services expose metrics at `/metrics`:
- `alerts_received_total` - Total alerts by severity
- `incidents_total` - Total incidents created
- `incident_mtta_seconds` - Mean Time To Acknowledge
- `incident_mttr_seconds` - Mean Time To Resolve

### Grafana Dashboards
1. **Live Incidents** - Real-time incident tracking and metrics
2. **SRE Performance** - MTTA, MTTR, alert distribution

Access: http://localhost:3001 (admin/admin)

## 🧪 Testing

### CI/CD Pipeline
```bash
# Run full pipeline (lint, test, build, deploy, verify)
bash scripts/ci-cd-pipeline.sh
```

Pipeline stages:
1. Code quality & testing
2. Build container images
3. Automated deployment
4. Post-deployment verification
5. Security scanning
6. Integration testing
7. Performance validation

### Health Checks
```bash
# Check all services
curl http://localhost:8001/health  # Alert Ingestion
curl http://localhost:8002/health  # Incident Management
curl http://localhost:8003/health  # On-Call Service
curl http://localhost:8004/health  # Notification Service
curl http://localhost:8080/health  # Web UI
```

## 📁 Project Structure

```
healthguard-ops/
├── services/
│   ├── alert-ingestion/          # Alert generation & processing
│   ├── incident-management/      # Incident lifecycle management
│   ├── oncall-service/           # Staff scheduling & auth
│   ├── notification-service/     # Real-time notifications
│   └── web-ui/                   # React frontend
├── monitoring/
│   ├── grafana-dashboards/       # Dashboard JSON definitions
│   └── prometheus/               # Prometheus config & rules
├── init-scripts/                 # Database initialization SQL
├── shared/                       # Modular SQL seed data
├── scripts/                      # Utility scripts
├── docker-compose.yml            # Service orchestration
└── .env.example                  # Environment template
```

## 🗄️ Database Schema

### Core Tables
- `employees` - 24 staff members (nurses, doctors, specialists)
- `patients` - 8 mock patients with room assignments
- `alert_type_definitions` - 33 hospital alert types
- `alerts` - Generated patient alerts
- `incidents` - Alert-triggered incidents
- `incident_assignments` - Staff-incident assignments
- `incident_history` - Audit trail
- `notifications` - Employee notifications
- `oncall_schedules` - Staff scheduling
- `escalation_policies` - Escalation rules

## 🔧 Troubleshooting

### Services not starting
```bash
# Stop everything
sudo docker-compose down

# Remove containers
sudo docker rm -f $(sudo docker ps -aq)

# Start fresh
sudo docker-compose up -d
```

### Database issues
```bash
# Reset database
sudo docker-compose down -v
sudo docker-compose up -d
```

### Metrics not showing in Grafana
```bash
# 1. Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# 2. Generate test data
for i in {1..10}; do curl -X POST http://localhost:8001/alerts/manual; sleep 1; done

# 3. Verify metrics exist
curl http://localhost:8001/metrics | grep alerts_received_total
```

## 🎯 Key Features

✅ **Real-time Alerts** - Automatic patient alert generation from medical devices
✅ **Smart Assignment** - Workload-based incident assignment to appropriate specialists
✅ **On-Call Scheduling** - 24/7 staff rotation management
✅ **Live Notifications** - WebSocket-based real-time updates
✅ **SRE Metrics** - Prometheus monitoring with MTTA/MTTR tracking
✅ **Incident Lifecycle** - OPEN → ASSIGNED → ACKNOWLEDGED → IN_PROGRESS → RESOLVED
✅ **Role-Based Routing** - Cardiac alerts → Cardiologists, Respiratory → Pulmonologists
✅ **Manual Claiming** - Staff can claim unassigned incidents
✅ **Audit Trail** - Complete incident history tracking

## 📄 API Endpoints

### Alert Ingestion (8001)
- `GET /health` - Health check
- `GET /alerts` - List all alerts
- `POST /alerts/manual` - Generate test alert
- `GET /metrics` - Prometheus metrics

### Incident Management (8002)
- `GET /api/incidents` - List incidents
- `GET /api/incidents/:id` - Get incident details
- `PATCH /api/incidents/:id/acknowledge` - Acknowledge incident
- `PATCH /api/incidents/:id/in-progress` - Start working on incident
- `PATCH /api/incidents/:id/resolve` - Resolve incident
- `PATCH /api/incidents/:id/claim` - Claim incident
- `GET /metrics` - Prometheus metrics

### On-Call Service (8003)
- `POST /auth/login` - Employee login
- `POST /auth/logout` - Employee logout
- `GET /oncall/current` - Current on-call staff
- `GET /metrics` - Prometheus metrics

### Notification Service (8004)
- `GET /notifications/:employee_id` - Get employee notifications
- `PATCH /notifications/:id/read` - Mark as read
- WebSocket: `/socket.io/` - Real-time notifications
- `GET /metrics` - Prometheus metrics

## 🔐 Security

- No hardcoded credentials (environment variables)
- CORS enabled for cross-origin requests
- PostgreSQL with password authentication
- RabbitMQ with default credentials (change in production)
- Health checks on all services

## 📝 Documentation

- **[CHEATSHEET.md](CHEATSHEET.md)** - Docker & DevOps commands
- **[INTEGRATION-SUMMARY.md](INTEGRATION-SUMMARY.md)** - Frontend integration notes
- **[MERGE-ANALYSIS.md](MERGE-ANALYSIS.md)** - Code merge analysis

---

**Built for Hackathon 2026** | Ready for production deployment with proper secrets management
