# HealthGuard Ops - System Architecture

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER LAYER                                  │
│                                                                          │
│  👨‍⚕️ Doctors  👩‍⚕️ Nurses  🧑‍⚕️ Specialists     📊 SRE Team              │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼────────┐       ┌───────▼────────┐
        │   Web Browser   │       │   Web Browser   │
        │  (Port 8080)    │       │  (Port 3001)    │
        └───────┬─────────┘       └───────┬─────────┘
                │                         │
                │                         │
┌───────────────▼─────────────────────────▼───────────────────────────────┐
│                        PRESENTATION LAYER                                │
│                                                                          │
│  ┌─────────────────────┐              ┌─────────────────────┐          │
│  │      Web UI          │              │      Grafana         │          │
│  │   (React + Vite)     │              │   (Dashboards)       │          │
│  │   nginx:8080         │              │      :3001           │          │
│  │                      │              │                      │          │
│  │  - Login/Auth        │              │  - Live Incidents    │          │
│  │  - Dashboard         │              │  - SRE Metrics       │          │
│  │  - Incidents         │              │  - MTTA/MTTR         │          │
│  │  - Alerts            │              │                      │          │
│  │  - On-Call           │              │                      │          │
│  │  - Metrics           │              │                      │          │
│  └──────────┬───────────┘              └──────────┬───────────┘          │
│             │                                     │                      │
└─────────────┼─────────────────────────────────────┼──────────────────────┘
              │                                     │
              │ HTTP/REST                           │ HTTP (PromQL)
              │ WebSocket                           │
              │                                     │
┌─────────────▼─────────────────────────────────────▼──────────────────────┐
│                        APPLICATION LAYER                                 │
│                                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Alert     │  │  Incident    │  │   On-Call    │  │ Notification │ │
│  │  Ingestion  │  │ Management   │  │   Service    │  │   Service    │ │
│  │   :8001     │  │    :8002     │  │    :8003     │  │    :8004     │ │
│  │             │  │              │  │              │  │              │ │
│  │ • Generate  │  │ • Lifecycle  │  │ • Auth       │  │ • WebSocket  │ │
│  │   Alerts    │  │ • Assignment │  │ • Schedules  │  │ • Push       │ │
│  │ • Validate  │  │ • Tracking   │  │ • Workload   │  │ • History    │ │
│  │ • Publish   │  │ • History    │  │ • Rotation   │  │              │ │
│  │             │  │              │  │              │  │              │ │
│  │ /metrics    │  │  /metrics    │  │  /metrics    │  │  /metrics    │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                │                 │                 │         │
└─────────┼────────────────┼─────────────────┼─────────────────┼─────────┘
          │                │                 │                 │
          │                │                 │                 │
          │   ┌────────────┴─────────────────┴─────────────────┤
          │   │                                                 │
┌─────────▼───▼─────────────────────────────────────────────────▼─────────┐
│                      INFRASTRUCTURE LAYER                                │
│                                                                          │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐      │
│  │   PostgreSQL    │   │    RabbitMQ     │   │   Prometheus    │      │
│  │     :5432       │   │  :5672, :15672  │   │     :9090       │      │
│  │                 │   │                 │   │                 │      │
│  │ • employees     │   │ • alerts queue  │   │ • Scrape        │      │
│  │ • patients      │   │ • notifications │   │   /metrics      │      │
│  │ • alerts        │   │ • Pub/Sub       │   │ • Time-series   │      │
│  │ • incidents     │   │                 │   │ • Alerting      │      │
│  │ • assignments   │   │                 │   │                 │      │
│  │ • history       │   │                 │   │                 │      │
│  └─────────────────┘   └─────────────────┘   └─────────────────┘      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow Diagrams

### 1. Alert Generation & Incident Creation Flow

```
┌─────────────┐
│  Medical    │  1. Alert triggered
│  Device     │     (e.g., Heart Rate > 140)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Alert Ingestion Service                                     │
│                                                              │
│  2. Fetch patient data from DB                              │
│  3. Fetch alert type definition                             │
│  4. Create alert record                                     │
│  5. Increment Prometheus counter (alerts_received_total)    │
└──────┬──────────────────────────┬───────────────────────────┘
       │                          │
       │ 6. Publish to            │ 7. Store in
       │    RabbitMQ              │    Database
       ▼                          ▼
┌─────────────┐          ┌─────────────┐
│  RabbitMQ   │          │ PostgreSQL  │
│   Queue     │          │   alerts    │
└──────┬──────┘          └─────────────┘
       │
       │ 8. Consume
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Incident Management Service                                 │
│                                                              │
│  9. Create incident from alert                              │
│  10. Determine required role (CARDIAC → CARDIOLOGIST)       │
│  11. Query On-Call Service for available staff             │
│  12. Calculate workload for each staff member              │
│  13. Assign to least busy staff                            │
│  14. Update Prometheus metrics (incidents_total)           │
│  15. Add to incident_history                               │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ 16. Publish notification
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Notification Service                                        │
│                                                              │
│  17. Store notification in DB                               │
│  18. Send via WebSocket to assigned staff                  │
│  19. Increment metrics (notifications_sent_total)          │
└──────────────────────────────────────────────────────────────┘
       │
       │ 20. Real-time push
       ▼
┌─────────────┐
│   Web UI    │  21. Display notification
│  (Browser)  │      Show incident details
└─────────────┘
```

### 2. Incident Lifecycle Flow

```
  OPEN
    │
    │ Staff reviews incident
    ▼
  ASSIGNED ──────────┐
    │                │
    │ Acknowledge    │ Claim by another staff
    ▼                ▼
ACKNOWLEDGED    REASSIGNED
    │                │
    │ Start work     │
    ▼                │
IN_PROGRESS ◄────────┘
    │
    │ Complete resolution
    ▼
 RESOLVED
    │
    │ Calculate metrics:
    │ • Response Time (OPEN → ACKNOWLEDGED)
    │ • Resolution Time (OPEN → RESOLVED)
    │ • Record MTTA, MTTR
    ▼
  [Archive]
```

### 3. Authentication & Authorization Flow

```
┌─────────────┐
│   Browser   │  1. Enter credentials
│   (Login)   │     (N01 / password123)
└──────┬──────┘
       │
       │ 2. POST /auth/login
       ▼
┌──────────────────────────────────────────────────────────────┐
│  On-Call Service                                             │
│                                                              │
│  3. Query employees table                                   │
│  4. Verify credentials (login + password)                   │
│  5. Update last_login, is_logged_in = TRUE                 │
│  6. Return employee data (id, name, role, tier)            │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ 7. Response with employee data
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Web UI (AuthContext)                                        │
│                                                              │
│  8. Store employee data in localStorage                     │
│  9. Set isAuthenticated = true                              │
│  10. Redirect to Dashboard                                  │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ 11. All subsequent requests include employee_id
       ▼
  Protected Routes
  (Dashboard, Incidents, etc.)
```

### 4. Monitoring & Metrics Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Application Services                                        │
│  (Alert, Incident, On-Call, Notification)                   │
│                                                              │
│  • Expose /metrics endpoint                                 │
│  • Increment counters on operations                         │
│  • Record histogram values for timing                       │
└──────┬──────────────────────────────────────────────────────┘
       │
       │ Scrape every 15s
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Prometheus                                                  │
│                                                              │
│  • Collect metrics from all services                        │
│  • Store time-series data                                   │
│  • Execute alerting rules                                   │
│  • Provide PromQL query interface                           │
└──────┬──────────────────────────────────────────────────────┘
       │
       │ Query metrics
       ▼
┌──────────────────────────────────────────────────────────────┐
│  Grafana                                                     │
│                                                              │
│  Dashboard 1: Live Incidents                                │
│  • sum(incidents_total)                                     │
│  • sum by (severity) (alerts_received_total)                │
│  • rate(incident_mtta_seconds_sum[5m])                      │
│                                                              │
│  Dashboard 2: SRE Performance                               │
│  • incident_mtta_seconds histogram                          │
│  • incident_mttr_seconds histogram                          │
│  • Alert distribution by severity                           │
└──────────────────────────────────────────────────────────────┘
       │
       │ Display
       ▼
  👨‍💻 SRE Team
```

## 🔌 Service Communication Matrix

| From Service | To Service | Protocol | Purpose |
|--------------|------------|----------|---------|
| Web UI | Alert Ingestion | HTTP REST | Fetch alerts, trigger manual alerts |
| Web UI | Incident Management | HTTP REST | View/manage incidents |
| Web UI | On-Call Service | HTTP REST | Login, fetch schedules |
| Web UI | Notification Service | WebSocket | Real-time notifications |
| Alert Ingestion | RabbitMQ | AMQP | Publish alerts |
| Alert Ingestion | PostgreSQL | TCP/IP | Store alerts |
| Incident Management | RabbitMQ | AMQP | Consume alerts |
| Incident Management | PostgreSQL | TCP/IP | Store/query incidents |
| Incident Management | On-Call Service | HTTP REST | Query available staff |
| Incident Management | Notification Service | RabbitMQ | Send notifications |
| On-Call Service | PostgreSQL | TCP/IP | Query employees, schedules |
| Notification Service | RabbitMQ | AMQP | Consume notifications |
| Notification Service | PostgreSQL | TCP/IP | Store notification history |
| Notification Service | Web UI | WebSocket | Push real-time updates |
| Prometheus | All Services | HTTP | Scrape /metrics endpoints |
| Grafana | Prometheus | HTTP | Query metrics (PromQL) |

## 📦 Component Details

### Frontend (Web UI)
- **Technology:** React 19, Vite, React Router 7
- **Server:** nginx (Alpine Linux)
- **Features:**
  - SPA with client-side routing
  - JWT-less authentication (session stored in localStorage)
  - Real-time WebSocket notifications
  - Context API for state management
- **Build:** Multi-stage Docker build (Node 18 → nginx Alpine)

### Backend Services
- **Technology:** Python 3.11, Flask, Flask-CORS
- **Common Libraries:**
  - `psycopg2-binary` - PostgreSQL driver
  - `pika` - RabbitMQ client
  - `prometheus-client` - Metrics exposition
  - `python-dotenv` - Environment variables

### Database
- **Technology:** PostgreSQL 15
- **Initialization:** Volume-mounted SQL scripts
- **Persistence:** Docker volume (postgres-data)
- **Seed Data:** 24 employees, 8 patients, 33 alert types

### Message Queue
- **Technology:** RabbitMQ 3.13 (management enabled)
- **Queues:**
  - `alerts` - Alert events from ingestion to incident
  - `notifications` - Notification events to staff
- **Features:** Durable queues, persistent messages

### Monitoring Stack
- **Prometheus:** Time-series metrics collection & alerting
- **Grafana:** Visualization & dashboards
- **Metrics Exposed:**
  - Counters: `alerts_received_total`, `incidents_total`, `notifications_sent_total`
  - Histograms: `incident_mtta_seconds`, `incident_mttr_seconds`
  - System: `up`, `process_*`, `python_*`

## 🔐 Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Security Layers                                             │
│                                                              │
│  1. Network Layer                                           │
│     • Docker internal network isolation                     │
│     • Port exposure only where needed                       │
│     • No direct database access from outside                │
│                                                              │
│  2. Application Layer                                       │
│     • CORS enabled for cross-origin requests                │
│     • Password verification (plaintext - for demo)          │
│     • Session management via localStorage                   │
│                                                              │
│  3. Data Layer                                              │
│     • PostgreSQL with password authentication               │
│     • No hardcoded credentials (env variables)              │
│     • Audit trail via incident_history table                │
│                                                              │
│  4. Transport Layer                                         │
│     • HTTP (HTTPS recommended for production)               │
│     • WebSocket for real-time (WSS for production)          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Deployment Architecture

```
┌───────────────────────────────────────────────────────────────┐
│  Docker Compose Orchestration                                 │
│                                                               │
│  Networks:                                                    │
│  • healthguard-ops_default (bridge)                          │
│                                                               │
│  Volumes:                                                     │
│  • postgres-data (database persistence)                      │
│  • rabbitmq-data (message queue persistence)                 │
│  • grafana-data (dashboard persistence)                      │
│  • prometheus-data (metrics persistence)                     │
│                                                               │
│  Health Checks:                                              │
│  • All services: 30s interval, 10s timeout, 3 retries       │
│  • Web UI: wget http://localhost:8080/health                │
│  • Backend: curl http://localhost:800X/health               │
│                                                               │
│  Restart Policy: unless-stopped                              │
└───────────────────────────────────────────────────────────────┘
```

## 📊 Scalability Considerations

### Current Architecture (Single Node)
- Suitable for: 50-100 concurrent users, ~1000 alerts/day
- Bottlenecks: Single PostgreSQL instance, in-memory queues

### Scaling Strategies

#### Horizontal Scaling
```
                    Load Balancer
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   Service 1         Service 2         Service 3
   (Replica)         (Replica)         (Replica)
        │                 │                 │
        └─────────────────┴─────────────────┘
                          │
                 Shared Database Pool
```

#### Microservices Optimization
- **Add API Gateway:** nginx/Kong for routing & rate limiting
- **Separate Read/Write:** PostgreSQL read replicas
- **Queue Clustering:** RabbitMQ cluster for HA
- **Caching Layer:** Redis for session & frequent queries
- **Service Mesh:** Istio/Linkerd for advanced traffic management

## 🎯 Design Principles

1. **Separation of Concerns:** Each service has a single responsibility
2. **Event-Driven:** Asynchronous processing via message queues
3. **Observable:** Comprehensive metrics at every layer
4. **Resilient:** Health checks, graceful degradation
5. **Maintainable:** Clear structure, documented APIs
6. **Scalable:** Stateless services, horizontal scaling ready

---

**Architecture Version:** 1.0
**Last Updated:** February 2026
**Status:** Production Ready
