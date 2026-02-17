-- ============================================================================
-- HealthGuard Ops - Database Initialization
-- Combined schema, reference data, and employee seed data
-- ============================================================================

-- ============================================================================
-- REFERENCE DATA TABLES (Patients, Rooms, Alert Type Definitions)
-- ============================================================================

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
-- EMPLOYEES TABLE (must be created before incidents, since incidents references it)
-- ============================================================================

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

-- ============================================================================
-- OPERATIONAL TABLES (Alerts, Incidents)
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
    alert_type VARCHAR(50),

    -- Status workflow: OPEN -> ASSIGNED -> ACKNOWLEDGED -> IN_PROGRESS -> RESOLVED
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
    response_time_seconds INTEGER,
    resolution_time_seconds INTEGER,
    total_time_seconds INTEGER,
    
    -- Notes and documentation
    resolution_notes TEXT,
    intermediate_notes TEXT[]
);

-- Incident history/audit trail
CREATE TABLE IF NOT EXISTS incident_history (
    history_id SERIAL PRIMARY KEY,
    incident_id VARCHAR(50) REFERENCES incidents(incident_id),
    employee_id INTEGER REFERENCES employees(employee_id),
    employee_name VARCHAR(100),
    action VARCHAR(50) NOT NULL,
    previous_status VARCHAR(20),
    new_status VARCHAR(20),
    note TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employees(employee_id),
    incident_id VARCHAR(50) REFERENCES incidents(incident_id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20),
    data JSONB,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
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

-- ============================================================================
-- INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_assigned_employee ON incidents(assigned_employee_id);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);
CREATE INDEX IF NOT EXISTS idx_incident_history_incident ON incident_history(incident_id);
CREATE INDEX IF NOT EXISTS idx_employees_logged_in ON employees(is_logged_in, role);
CREATE INDEX IF NOT EXISTS idx_notifications_employee ON notifications(employee_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

-- ============================================================================
-- SEED DATA: PATIENTS
-- ============================================================================

INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, gender, room, admission_date, status, medical_record_number, blood_type, allergies) VALUES
('P4521', 'John', 'Smith', '1965-03-15', 'M', '312', NOW() - INTERVAL '2 days', 'CRITICAL', 'MRN001', 'O+', 'Penicillin'),
('P2103', 'Sarah', 'Johnson', '1978-07-22', 'F', '205', NOW() - INTERVAL '1 day', 'ADMITTED', 'MRN002', 'A+', 'None'),
('P7788', 'Michael', 'Chen', '1982-11-30', 'M', '401', NOW() - INTERVAL '3 days', 'ADMITTED', 'MRN003', 'B+', 'Latex'),
('P3344', 'Emma', 'Williams', '1990-05-18', 'F', '108', NOW() - INTERVAL '5 hours', 'CRITICAL', 'MRN004', 'AB-', 'Sulfa drugs'),
('P5566', 'David', 'Brown', '1955-09-08', 'M', '523', NOW() - INTERVAL '4 days', 'CRITICAL', 'MRN005', 'O-', 'Aspirin'),
('P8899', 'Lisa', 'Garcia', '1988-12-25', 'F', '614', NOW() - INTERVAL '1 day', 'ADMITTED', 'MRN006', 'A-', 'None'),
('P1122', 'James', 'Martinez', '1970-04-12', 'M', '307', NOW() - INTERVAL '6 hours', 'ADMITTED', 'MRN007', 'B-', 'Iodine'),
('P6677', 'Maria', 'Rodriguez', '1995-08-03', 'F', '501', NOW() - INTERVAL '2 days', 'ADMITTED', 'MRN008', 'AB+', 'None')
ON CONFLICT (patient_id) DO NOTHING;

-- ============================================================================
-- SEED DATA: ROOMS
-- ============================================================================

INSERT INTO rooms (room_number, floor, room_type, capacity, is_occupied, current_patient_id) VALUES
('312', 3, 'ICU', 1, TRUE, 'P4521'),
('205', 2, 'GENERAL', 2, TRUE, 'P2103'),
('401', 4, 'GENERAL', 2, TRUE, 'P7788'),
('108', 1, 'EMERGENCY', 1, TRUE, 'P3344'),
('523', 5, 'ICU', 1, TRUE, 'P5566'),
('614', 6, 'MATERNITY', 2, TRUE, 'P8899'),
('307', 3, 'GENERAL', 2, TRUE, 'P1122'),
('501', 5, 'GENERAL', 2, TRUE, 'P6677')
ON CONFLICT (room_number) DO NOTHING;

-- ============================================================================
-- SEED DATA: ALERT TYPE DEFINITIONS
-- ============================================================================

INSERT INTO alert_type_definitions (alert_type, severity, category, description, requires_immediate_response, typical_values) VALUES
('CARDIAC_ARREST', 'CRITICAL', 'CARDIAC', 'Heart stopped, needs immediate CPR', TRUE, 
 ARRAY['Asystole', 'Ventricular fibrillation', 'No pulse detected']),
('CARDIAC_ABNORMAL', 'CRITICAL', 'CARDIAC', 'Irregular heartbeat, arrhythmia', TRUE,
 ARRAY['Tachycardia 145bpm', 'Bradycardia 35bpm', 'Arrhythmia detected', 'Atrial fibrillation']),
('MYOCARDIAL_INFARCTION', 'CRITICAL', 'CARDIAC', 'Heart attack detected', TRUE,
 ARRAY['ST elevation detected', 'Chest pain + ECG changes', 'Troponin elevated']),
('RESPIRATORY_DISTRESS', 'CRITICAL', 'RESPIRATORY', 'Difficulty breathing, respiratory failure', TRUE,
 ARRAY['Labored breathing', 'Respiratory rate 35/min', 'Accessory muscle use']),
('O2_SATURATION_LOW', 'CRITICAL', 'RESPIRATORY', 'Blood oxygen below 90%', TRUE,
 ARRAY['SpO2 at 82%', 'SpO2 at 78%', 'SpO2 at 85%']),
('APNEA_DETECTED', 'CRITICAL', 'RESPIRATORY', 'Patient stopped breathing', TRUE,
 ARRAY['Breathing stopped', 'No respiratory effort', 'Apnea alarm']),
('VENTILATOR_ALARM', 'CRITICAL', 'RESPIRATORY', 'Ventilator malfunction or disconnect', TRUE,
 ARRAY['High pressure alarm', 'Low volume alarm', 'Disconnect detected']),
('STROKE_SUSPECTED', 'CRITICAL', 'NEUROLOGICAL', 'Possible stroke symptoms detected', TRUE,
 ARRAY['Facial drooping', 'Arm weakness', 'Speech difficulty', 'FAST protocol positive']),
('SEIZURE_DETECTED', 'HIGH', 'NEUROLOGICAL', 'Patient experiencing seizure', TRUE,
 ARRAY['Tonic-clonic activity', 'Post-ictal state', 'Status epilepticus']),
('INTRACRANIAL_PRESSURE_HIGH', 'CRITICAL', 'NEUROLOGICAL', 'Dangerous brain pressure', TRUE,
 ARRAY['ICP 25mmHg', 'ICP 30mmHg', 'Dangerous brain pressure']),
('HYPERTENSION_CRISIS', 'HIGH', 'BLOOD_PRESSURE', 'Dangerously high blood pressure', TRUE,
 ARRAY['BP 200/120', 'BP 210/130', 'Hypertensive emergency']),
('HYPOTENSION_SEVERE', 'HIGH', 'BLOOD_PRESSURE', 'Dangerously low blood pressure', TRUE,
 ARRAY['BP 70/40', 'BP 65/35', 'Hypotensive shock']),
('HEMORRHAGE_MAJOR', 'CRITICAL', 'TRAUMA', 'Major internal or external bleeding', TRUE,
 ARRAY['Severe bleeding', 'Hemoglobin 6g/dL', 'Blood loss >1000ml']),
('TRAUMA_SEVERE', 'CRITICAL', 'TRAUMA', 'Severe traumatic injury', TRUE,
 ARRAY['Multiple injuries', 'Head trauma', 'Blunt force trauma']),
('HYPOGLYCEMIA_SEVERE', 'HIGH', 'METABOLIC', 'Blood sugar critically low', TRUE,
 ARRAY['Glucose 35mg/dL', 'Glucose 40mg/dL', 'Altered consciousness']),
('HYPERGLYCEMIA_SEVERE', 'HIGH', 'METABOLIC', 'Blood sugar critically high', TRUE,
 ARRAY['Glucose 450mg/dL', 'Glucose 500mg/dL', 'DKA suspected']),
('DIABETIC_KETOACIDOSIS', 'CRITICAL', 'METABOLIC', 'Life-threatening diabetes complication', TRUE,
 ARRAY['pH 7.1 + Ketones', 'DKA confirmed', 'Metabolic acidosis']),
('SEPSIS_SUSPECTED', 'CRITICAL', 'INFECTION', 'Life-threatening infection response', TRUE,
 ARRAY['Temp 39.5C + Hypotension', 'SIRS criteria met', 'Lactate 4.2']),
('FEVER_HIGH', 'MEDIUM', 'INFECTION', 'Temperature above 39C/102F', FALSE,
 ARRAY['Temperature 39.8C', 'Temperature 40.1C', 'Fever spike']),
('MEDICATION_DELAYED', 'MEDIUM', 'MEDICATION', 'Scheduled medication not administered', FALSE,
 ARRAY['Insulin 30min overdue', 'Antibiotic 45min overdue', 'Critical med delayed']),
('MEDICATION_ERROR', 'HIGH', 'MEDICATION', 'Wrong medication or dosage detected', TRUE,
 ARRAY['Wrong dosage detected', 'Drug interaction alert', 'Contraindicated medication']),
('ADVERSE_REACTION', 'HIGH', 'MEDICATION', 'Allergic or adverse drug reaction', TRUE,
 ARRAY['Allergic reaction', 'Anaphylaxis suspected', 'Drug adverse effect']),
('IV_INFILTRATION', 'MEDIUM', 'MEDICATION', 'IV fluid leaking into tissue', FALSE,
 ARRAY['IV site swollen', 'Fluid leaking', 'IV infiltrated']),
('EQUIPMENT_MALFUNCTION', 'HIGH', 'EQUIPMENT', 'Critical equipment failure', TRUE,
 ARRAY['Monitor disconnected', 'Pump occlusion', 'Device failure']),
('EQUIPMENT_LOW_BATTERY', 'MEDIUM', 'EQUIPMENT', 'Medical device battery low', FALSE,
 ARRAY['Monitor battery 10%', 'Pump battery 15%', 'Ventilator backup power']),
('FALL_DETECTED', 'HIGH', 'SAFETY', 'Patient fallen, possible injury', TRUE,
 ARRAY['Impact sensor triggered', 'Patient on floor', 'Head strike detected']),
('BED_EXIT_UNAUTHORIZED', 'MEDIUM', 'SAFETY', 'High-risk patient left bed', FALSE,
 ARRAY['High-risk patient left bed', 'Bed alarm triggered', 'Wandering patient']),
('RESTRAINT_ALERT', 'HIGH', 'SAFETY', 'Patient in distress with restraints', TRUE,
 ARRAY['Patient distressed', 'Restraint check needed', 'Agitation with restraints']),
('FETAL_DISTRESS', 'CRITICAL', 'OBSTETRIC', 'Baby showing signs of distress', TRUE,
 ARRAY['Fetal heart rate 100bpm', 'Late decelerations', 'Cord prolapse suspected']),
('LABOR_COMPLICATIONS', 'HIGH', 'OBSTETRIC', 'Complications during labor', TRUE,
 ARRAY['Prolonged labor', 'Maternal distress', 'Emergency C-section needed']),
('AGITATION_SEVERE', 'HIGH', 'PSYCHIATRIC', 'Patient severely agitated or violent', TRUE,
 ARRAY['Combative behavior', 'Verbally threatening', 'Physical aggression']),
('SUICIDE_RISK', 'CRITICAL', 'PSYCHIATRIC', 'Patient expressing suicidal ideation', TRUE,
 ARRAY['Suicidal ideation expressed', 'Self-harm attempt', 'Psychiatric emergency'])
ON CONFLICT (alert_type) DO NOTHING;

-- ============================================================================
-- SEED DATA: EMPLOYEES
-- ============================================================================

INSERT INTO employees (login, password, name, email, phone, role, tier, shift_start_time, shift_end_time) VALUES
-- POLYVALENT NURSES - Day shift (8AM - 4PM)
('N01', 'password123', 'Sarah Johnson', 'sarah.johnson@hospital.com', '555-0101', 'NURSE', 1, '08:00:00', '16:00:00'),
('N02', 'password123', 'Lisa Wong', 'lisa.wong@hospital.com', '555-0102', 'NURSE', 1, '08:00:00', '16:00:00'),

-- POLYVALENT NURSES - Evening shift (4PM - 12AM)
('N03', 'password123', 'Mike Chen', 'mike.chen@hospital.com', '555-0103', 'NURSE', 2, '16:00:00', '00:00:00'),
('N04', 'password123', 'Emma Martinez', 'emma.martinez@hospital.com', '555-0104', 'NURSE', 2, '16:00:00', '00:00:00'),

-- POLYVALENT NURSES - Night shift (12AM - 8AM)
('N05', 'password123', 'David Park', 'david.park@hospital.com', '555-0105', 'NURSE', 3, '00:00:00', '08:00:00'),
('N06', 'password123', 'Rachel Green', 'rachel.green@hospital.com', '555-0106', 'NURSE', 3, '00:00:00', '08:00:00'),

-- EMERGENCY DOCTORS - Day shift (8AM - 4PM)
('D01', 'password123', 'Dr. Robert Chen', 'robert.chen@hospital.com', '555-0201', 'EMERGENCY_DOCTOR', 1, '08:00:00', '16:00:00'),

-- EMERGENCY DOCTORS - Evening shift (4PM - 12AM)
('D02', 'password123', 'Dr. Maria Rodriguez', 'maria.rodriguez@hospital.com', '555-0202', 'EMERGENCY_DOCTOR', 2, '16:00:00', '00:00:00'),
('D03', 'password123', 'Dr. James Wilson', 'james.wilson@hospital.com', '555-0203', 'EMERGENCY_DOCTOR', 2, '16:00:00', '00:00:00'),

-- EMERGENCY DOCTORS - Night shift (12AM - 8AM)
('D04', 'password123', 'Dr. Amanda Lee', 'amanda.lee@hospital.com', '555-0204', 'EMERGENCY_DOCTOR', 3, '00:00:00', '08:00:00'),

-- CARDIOLOGIST - Day shift (8AM - 4PM)
('S01', 'password123', 'Dr. Michael Thompson', 'michael.thompson@hospital.com', '555-0301', 'CARDIOLOGIST', 1, '08:00:00', '16:00:00'),
('S02', 'password123', 'Dr. Jennifer Adams', 'jennifer.adams@hospital.com', '555-0302', 'CARDIOLOGIST', 1, '08:00:00', '16:00:00'),

-- PULMONOLOGIST
('S03', 'password123', 'Dr. Daniel Kim', 'daniel.kim@hospital.com', '555-0303', 'PULMONOLOGIST', 1, '08:00:00', '16:00:00'),

-- NEUROLOGIST
('S04', 'password123', 'Dr. Patricia Brown', 'patricia.brown@hospital.com', '555-0304', 'NEUROLOGIST', 1, '08:00:00', '16:00:00'),
('S05', 'password123', 'Dr. Ahmed Hassan', 'ahmed.hassan@hospital.com', '555-0305', 'NEUROLOGIST', 1, '08:00:00', '16:00:00'),

-- SURGEON
('S06', 'password123', 'Dr. Susan Miller', 'susan.miller@hospital.com', '555-0306', 'SURGEON', 1, '08:00:00', '16:00:00'),
('S07', 'password123', 'Dr. David Cohen', 'david.cohen@hospital.com', '555-0307', 'SURGEON', 2, '16:00:00', '00:00:00'),

-- OBSTETRICIAN
('S08', 'password123', 'Dr. Laura Martinez', 'laura.martinez@hospital.com', '555-0308', 'OBSTETRICIAN', 1, '08:00:00', '16:00:00'),
('S09', 'password123', 'Dr. Kevin Nguyen', 'kevin.nguyen@hospital.com', '555-0309', 'OBSTETRICIAN', 2, '16:00:00', '00:00:00'),

-- PSYCHIATRIST
('S10', 'password123', 'Dr. Elizabeth Taylor', 'elizabeth.taylor@hospital.com', '555-0310', 'PSYCHIATRIST', 1, '08:00:00', '16:00:00'),

-- ENDOCRINOLOGIST
('S11', 'password123', 'Dr. William Garcia', 'william.garcia@hospital.com', '555-0311', 'ENDOCRINOLOGIST', 1, '08:00:00', '16:00:00'),

-- INFECTIOUS_DISEASE
('S12', 'password123', 'Dr. Sophia Anderson', 'sophia.anderson@hospital.com', '555-0312', 'INFECTIOUS_DISEASE', 1, '08:00:00', '16:00:00'),

-- BIOMEDICAL ENGINEERS
('E01', 'password123', 'Alex Rivera', 'alex.rivera@hospital.com', '555-0401', 'BIOMEDICAL_ENGINEER', 1, '08:00:00', '16:00:00'),
('E02', 'password123', 'Jessica Martinez', 'jessica.martinez@hospital.com', '555-0402', 'BIOMEDICAL_ENGINEER', 1, '08:00:00', '16:00:00')
ON CONFLICT (login) DO NOTHING;

-- ============================================================================
-- GRANTS & PERMISSIONS
-- ============================================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;

-- Log initialization
SELECT 'Database initialization completed successfully' as status;
