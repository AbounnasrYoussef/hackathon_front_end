# Patient Care Escalation Platform

A hospital incident management system built with microservices architecture for hackathon.

## Architecture

- **Alert Service** (Port 8001): Generates fake patient alerts and publishes to RabbitMQ
- **Incident Service** (Port 8002): Consumes alerts, creates incidents, manages incident lifecycle
- **On-Call Service** (Port 8003): Manages on-call schedules and assigns incidents

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Message Queue**: RabbitMQ
- **CORS**: Enabled for all services

## Project Structure

```
patient-care-platform/
├── alert-service/
│   ├── app.py
│   └── requirements.txt
├── incident-service/
│   ├── app.py
│   └── requirements.txt
├── oncall-service/
│   ├── app.py
│   └── requirements.txt
├── shared/
│   └── schema.sql
├── .env.example
└── README.md
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- PostgreSQL
- RabbitMQ

### 2. Database Setup

```bash
# Create database
createdb hospital

# Run schema
psql -d hospital -f shared/schema.sql
```

### 3. Environment Configuration

Copy `.env.example` to `.env` in each service directory and adjust as needed:

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/hospital
RABBITMQ_HOST=localhost
```

### 4. Install Dependencies

For each service:

```bash
cd alert-service
pip install -r requirements.txt

cd ../incident-service
pip install -r requirements.txt

cd ../oncall-service
pip install -r requirements.txt
```

### 5. Run Services

**Terminal 1 - Alert Service:**
```bash
cd alert-service
python app.py
```

**Terminal 2 - Incident Service:**
```bash
cd incident-service
python app.py
```

**Terminal 3 - On-Call Service:**
```bash
cd oncall-service
python app.py
```

## API Endpoints

### Alert Service (Port 8001)

- `GET /health` - Health check
- `GET /alerts` - Get all alerts
- `POST /alerts/manual` - Manually trigger an alert

### Incident Service (Port 8002)

- `GET /health` - Health check
- `GET /incidents?status=OPEN` - Get incidents (filter by status)
- `GET /incidents/{id}` - Get specific incident
- `PATCH /incidents/{id}/acknowledge` - Acknowledge incident
- `PATCH /incidents/{id}/resolve` - Resolve incident with notes
- `GET /incidents/metrics` - Get metrics (avg response time, counts)

### On-Call Service (Port 8003)

- `GET /health` - Health check
- `GET /oncall/current?role=CARDIOLOGY_NURSE` - Get current on-call person
- `POST /oncall/assign` - Assign incident to on-call person
- `GET /oncall/schedules` - Get all schedules

## Alert Types

- `CARDIAC_ABNORMAL` (CRITICAL)
- `MEDICATION_DELAYED` (MEDIUM)
- `EQUIPMENT_LOW_BATTERY` (HIGH)
- `O2_SATURATION_LOW` (CRITICAL)

## Fake Data

**Patients**: P4521, P2103, P7788, P3344, P5566  
**Rooms**: 312, 205, 401, 108, 523

## On-Call Roles

- `CARDIOLOGY_NURSE`: Sarah Johnson (Tier 1), Mike Chen (Tier 2)
- `ICU_NURSE`: Lisa Wong (Tier 1), David Park (Tier 2)
- `BIOMEDICAL_ENGINEER`: Alex Rivera (Tier 1)

## Features

✅ Automatic alert generation (every 10-30 seconds)  
✅ RabbitMQ message queue integration  
✅ PostgreSQL database for persistence  
✅ Incident lifecycle management  
✅ On-call schedule management  
✅ Metrics and analytics  
✅ Error handling and retry logic  
✅ CORS enabled for frontend integration

## Development Notes

- Alert service generates alerts automatically in background thread
- Incident service listens to RabbitMQ queue in background thread
- All services include proper error handling and logging
- Retry logic implemented for RabbitMQ connections (5 attempts, 5s delay)
- IDs generated as `ALT-{timestamp}` and `INC-{timestamp}`
