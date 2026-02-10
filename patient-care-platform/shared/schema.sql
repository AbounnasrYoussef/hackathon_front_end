-- Patient Care Platform Database Schema
-- ============================================================================

-- ============================================================================
-- REFERENCE DATA TABLES (Patients, Rooms, Alert Type Definitions)
-- ============================================================================
-- These tables are defined in reference_data.sql

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    room VARCHAR(10),
    admission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ADMITTED',
    medical_record_number VARCHAR(20) UNIQUE,
    blood_type VARCHAR(5),
    allergies TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rooms table
CREATE TABLE IF NOT EXISTS rooms (
    room_number VARCHAR(10) PRIMARY KEY,
    floor INTEGER NOT NULL,
    room_type VARCHAR(30) NOT NULL,
    capacity INTEGER DEFAULT 1,
    is_occupied BOOLEAN DEFAULT FALSE,
    current_patient_id VARCHAR(20) REFERENCES patients(patient_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Alert type definitions table
CREATE TABLE IF NOT EXISTS alert_type_definitions (
    alert_type VARCHAR(50) PRIMARY KEY,
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    requires_immediate_response BOOLEAN DEFAULT TRUE,
    typical_values TEXT[] NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- OPERATIONAL TABLES (Alerts, Incidents, Employees)
-- ============================================================================

-- Alerts table
CREATE TABLE IF NOT EXISTS alerts (
    alert_id VARCHAR(50) PRIMARY KEY,
    patient_id VARCHAR(20) NOT NULL,
    room VARCHAR(10),
    alert_type VARCHAR(50),
    severity VARCHAR(20),
    value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enhanced Incidents table with full workflow tracking
CREATE TABLE IF NOT EXISTS incidents (
    incident_id VARCHAR(50) PRIMARY KEY,
    alert_id VARCHAR(50) REFERENCES alerts(alert_id),
    patient_id VARCHAR(20),
    room VARCHAR(10),
    alert_type VARCHAR(100),
    
    -- Status workflow: OPEN → ASSIGNED → ACKNOWLEDGED → IN_PROGRESS → RESOLVED
    status VARCHAR(20) DEFAULT 'OPEN',
    severity VARCHAR(20),
    
    -- Employee tracking
    assigned_to VARCHAR(100),
    assigned_employee_id INTEGER REFERENCES employees(employee_id),
    resolved_by_employee_id INTEGER REFERENCES employees(employee_id),
    
    -- Timestamps for workflow stages
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    in_progress_at TIMESTAMP,
    resolved_at TIMESTAMP,
    
    -- Time metrics (calculated automatically)
    response_time_seconds INTEGER, -- Time from OPEN to ACKNOWLEDGED
    resolution_time_seconds INTEGER, -- Time from ACKNOWLEDGED to RESOLVED
    total_time_seconds INTEGER, -- Time from OPEN to RESOLVED
    
    -- Notes and documentation
    resolution_notes TEXT, -- Final outcome notes (required on resolve)
    intermediate_notes TEXT[] -- Array of progress updates during work
);

-- Incident history/audit trail
CREATE TABLE IF NOT EXISTS incident_history (
    history_id SERIAL PRIMARY KEY,
    incident_id VARCHAR(50) REFERENCES incidents(incident_id),
    employee_id INTEGER REFERENCES employees(employee_id),
    employee_name VARCHAR(100),
    action VARCHAR(50) NOT NULL, -- CREATED, ASSIGNED, ACKNOWLEDGED, NOTE_ADDED, STATUS_CHANGED, RESOLVED
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    note TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Incident assignments (many-to-many: one incident can be assigned to multiple staff)
CREATE TABLE IF NOT EXISTS incident_assignments (
    assignment_id SERIAL PRIMARY KEY,
    incident_id VARCHAR(50) REFERENCES incidents(incident_id),
    employee_id INTEGER REFERENCES employees(employee_id),
    employee_name VARCHAR(100),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    UNIQUE(incident_id, employee_id)
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id),
    incident_id VARCHAR(50) REFERENCES incidents(incident_id),
    type VARCHAR(50) NOT NULL, -- INCIDENT_ASSIGNED, INCIDENT_ESCALATED, SHIFT_REMINDER, etc.
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20), -- CRITICAL, HIGH, MEDIUM, LOW
    data JSONB, -- Additional data as JSON
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees/Staff table
CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    login VARCHAR(20) UNIQUE NOT NULL,
    password VARCHAR(100) NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    role VARCHAR(50) NOT NULL,
    tier INTEGER NOT NULL,
    shift_start_time TIME NOT NULL,
    shift_end_time TIME NOT NULL,
    is_logged_in BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- On-call schedules (links employees to shifts)
CREATE TABLE IF NOT EXISTS oncall_schedules (
    schedule_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id),
    role VARCHAR(50),
    person_name VARCHAR(100),
    tier INTEGER,
    shift_start TIMESTAMP,
    shift_end TIMESTAMP
);

-- Escalation policies
CREATE TABLE IF NOT EXISTS escalation_policies (
    policy_id VARCHAR(50) PRIMARY KEY,
    incident_type VARCHAR(50),
    tier INTEGER,
    role VARCHAR(50),
    timeout_seconds INTEGER
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned_employee ON incidents(assigned_employee_id);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);
CREATE INDEX IF NOT EXISTS idx_incident_history_incident ON incident_history(incident_id);
CREATE INDEX IF NOT EXISTS idx_employees_logged_in ON employees(is_logged_in, role);
CREATE INDEX IF NOT EXISTS idx_notifications_employee ON notifications(employee_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
