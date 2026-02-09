-- Reference Data Tables for Patient Care Platform
-- This file contains mock data for patients, rooms, and alert type definitions

-- ============================================================================
-- PATIENTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(20) PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(10) NOT NULL,
    room VARCHAR(10),
    admission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'ADMITTED', -- ADMITTED, DISCHARGED, CRITICAL
    medical_record_number VARCHAR(20) UNIQUE,
    blood_type VARCHAR(5),
    allergies TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ROOMS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS rooms (
    room_number VARCHAR(10) PRIMARY KEY,
    floor INTEGER NOT NULL,
    room_type VARCHAR(30) NOT NULL, -- ICU, GENERAL, EMERGENCY, MATERNITY, PSYCHIATRIC
    capacity INTEGER DEFAULT 1,
    is_occupied BOOLEAN DEFAULT FALSE,
    current_patient_id VARCHAR(20) REFERENCES patients(patient_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ALERT TYPE DEFINITIONS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS alert_type_definitions (
    alert_type VARCHAR(50) PRIMARY KEY,
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL, -- CARDIAC, RESPIRATORY, NEUROLOGICAL, etc.
    description TEXT,
    requires_immediate_response BOOLEAN DEFAULT TRUE,
    typical_values TEXT[] NOT NULL, -- Array of possible values
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INSERT MOCK PATIENTS
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
-- INSERT ROOMS
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
-- INSERT ALERT TYPE DEFINITIONS
-- ============================================================================
INSERT INTO alert_type_definitions (alert_type, severity, category, description, requires_immediate_response, typical_values) VALUES
-- CARDIAC/CARDIOVASCULAR
('CARDIAC_ARREST', 'CRITICAL', 'CARDIAC', 'Heart stopped, needs immediate CPR', TRUE, 
 ARRAY['Asystole', 'Ventricular fibrillation', 'No pulse detected']),
('CARDIAC_ABNORMAL', 'CRITICAL', 'CARDIAC', 'Irregular heartbeat, arrhythmia', TRUE,
 ARRAY['Tachycardia 145bpm', 'Bradycardia 35bpm', 'Arrhythmia detected', 'Atrial fibrillation']),
('MYOCARDIAL_INFARCTION', 'CRITICAL', 'CARDIAC', 'Heart attack detected', TRUE,
 ARRAY['ST elevation detected', 'Chest pain + ECG changes', 'Troponin elevated']),

-- RESPIRATORY
('RESPIRATORY_DISTRESS', 'CRITICAL', 'RESPIRATORY', 'Difficulty breathing, respiratory failure', TRUE,
 ARRAY['Labored breathing', 'Respiratory rate 35/min', 'Accessory muscle use']),
('O2_SATURATION_LOW', 'CRITICAL', 'RESPIRATORY', 'Blood oxygen below 90%', TRUE,
 ARRAY['SpO2 at 82%', 'SpO2 at 78%', 'SpO2 at 85%']),
('APNEA_DETECTED', 'CRITICAL', 'RESPIRATORY', 'Patient stopped breathing', TRUE,
 ARRAY['Breathing stopped', 'No respiratory effort', 'Apnea alarm']),
('VENTILATOR_ALARM', 'CRITICAL', 'RESPIRATORY', 'Ventilator malfunction or disconnect', TRUE,
 ARRAY['High pressure alarm', 'Low volume alarm', 'Disconnect detected']),

-- NEUROLOGICAL
('STROKE_SUSPECTED', 'CRITICAL', 'NEUROLOGICAL', 'Possible stroke symptoms detected', TRUE,
 ARRAY['Facial drooping', 'Arm weakness', 'Speech difficulty', 'FAST protocol positive']),
('SEIZURE_DETECTED', 'HIGH', 'NEUROLOGICAL', 'Patient experiencing seizure', TRUE,
 ARRAY['Tonic-clonic activity', 'Post-ictal state', 'Status epilepticus']),
('INTRACRANIAL_PRESSURE_HIGH', 'CRITICAL', 'NEUROLOGICAL', 'Dangerous brain pressure', TRUE,
 ARRAY['ICP 25mmHg', 'ICP 30mmHg', 'Dangerous brain pressure']),

-- BLOOD PRESSURE
('HYPERTENSION_CRISIS', 'HIGH', 'BLOOD_PRESSURE', 'Dangerously high blood pressure', TRUE,
 ARRAY['BP 200/120', 'BP 210/130', 'Hypertensive emergency']),
('HYPOTENSION_SEVERE', 'HIGH', 'BLOOD_PRESSURE', 'Dangerously low blood pressure', TRUE,
 ARRAY['BP 70/40', 'BP 65/35', 'Hypotensive shock']),

-- BLEEDING/TRAUMA
('HEMORRHAGE_MAJOR', 'CRITICAL', 'TRAUMA', 'Major internal or external bleeding', TRUE,
 ARRAY['Severe bleeding', 'Hemoglobin 6g/dL', 'Blood loss >1000ml']),
('TRAUMA_SEVERE', 'CRITICAL', 'TRAUMA', 'Severe traumatic injury', TRUE,
 ARRAY['Multiple injuries', 'Head trauma', 'Blunt force trauma']),

-- GLUCOSE/METABOLIC
('HYPOGLYCEMIA_SEVERE', 'HIGH', 'METABOLIC', 'Blood sugar critically low', TRUE,
 ARRAY['Glucose 35mg/dL', 'Glucose 40mg/dL', 'Altered consciousness']),
('HYPERGLYCEMIA_SEVERE', 'HIGH', 'METABOLIC', 'Blood sugar critically high', TRUE,
 ARRAY['Glucose 450mg/dL', 'Glucose 500mg/dL', 'DKA suspected']),
('DIABETIC_KETOACIDOSIS', 'CRITICAL', 'METABOLIC', 'Life-threatening diabetes complication', TRUE,
 ARRAY['pH 7.1 + Ketones', 'DKA confirmed', 'Metabolic acidosis']),

-- INFECTION/SEPSIS
('SEPSIS_SUSPECTED', 'CRITICAL', 'INFECTION', 'Life-threatening infection response', TRUE,
 ARRAY['Temp 39.5°C + Hypotension', 'SIRS criteria met', 'Lactate 4.2']),
('FEVER_HIGH', 'MEDIUM', 'INFECTION', 'Temperature above 39°C/102°F', FALSE,
 ARRAY['Temperature 39.8°C', 'Temperature 40.1°C', 'Fever spike']),

-- MEDICATION/TREATMENT
('MEDICATION_DELAYED', 'MEDIUM', 'MEDICATION', 'Scheduled medication not administered', FALSE,
 ARRAY['Insulin 30min overdue', 'Antibiotic 45min overdue', 'Critical med delayed']),
('MEDICATION_ERROR', 'HIGH', 'MEDICATION', 'Wrong medication or dosage detected', TRUE,
 ARRAY['Wrong dosage detected', 'Drug interaction alert', 'Contraindicated medication']),
('ADVERSE_REACTION', 'HIGH', 'MEDICATION', 'Allergic or adverse drug reaction', TRUE,
 ARRAY['Allergic reaction', 'Anaphylaxis suspected', 'Drug adverse effect']),
('IV_INFILTRATION', 'MEDIUM', 'MEDICATION', 'IV fluid leaking into tissue', FALSE,
 ARRAY['IV site swollen', 'Fluid leaking', 'IV infiltrated']),

-- EQUIPMENT/TECHNICAL
('EQUIPMENT_MALFUNCTION', 'HIGH', 'EQUIPMENT', 'Critical equipment failure', TRUE,
 ARRAY['Monitor disconnected', 'Pump occlusion', 'Device failure']),
('EQUIPMENT_LOW_BATTERY', 'MEDIUM', 'EQUIPMENT', 'Medical device battery low', FALSE,
 ARRAY['Monitor battery 10%', 'Pump battery 15%', 'Ventilator backup power']),

-- PATIENT SAFETY
('FALL_DETECTED', 'HIGH', 'SAFETY', 'Patient fallen, possible injury', TRUE,
 ARRAY['Impact sensor triggered', 'Patient on floor', 'Head strike detected']),
('BED_EXIT_UNAUTHORIZED', 'MEDIUM', 'SAFETY', 'High-risk patient left bed', FALSE,
 ARRAY['High-risk patient left bed', 'Bed alarm triggered', 'Wandering patient']),
('RESTRAINT_ALERT', 'HIGH', 'SAFETY', 'Patient in distress with restraints', TRUE,
 ARRAY['Patient distressed', 'Restraint check needed', 'Agitation with restraints']),

-- OBSTETRIC
('FETAL_DISTRESS', 'CRITICAL', 'OBSTETRIC', 'Baby showing signs of distress', TRUE,
 ARRAY['Fetal heart rate 100bpm', 'Late decelerations', 'Cord prolapse suspected']),
('LABOR_COMPLICATIONS', 'HIGH', 'OBSTETRIC', 'Complications during labor', TRUE,
 ARRAY['Prolonged labor', 'Maternal distress', 'Emergency C-section needed']),

-- PSYCHIATRIC
('AGITATION_SEVERE', 'HIGH', 'PSYCHIATRIC', 'Patient severely agitated or violent', TRUE,
 ARRAY['Combative behavior', 'Verbally threatening', 'Physical aggression']),
('SUICIDE_RISK', 'CRITICAL', 'PSYCHIATRIC', 'Patient expressing suicidal ideation', TRUE,
 ARRAY['Suicidal ideation expressed', 'Self-harm attempt', 'Psychiatric emergency'])
ON CONFLICT (alert_type) DO NOTHING;
