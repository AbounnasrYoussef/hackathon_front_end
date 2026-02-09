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

-- Insert mock employees data with shift times, login IDs, and passwords
-- Login format: N## for Nurses, D## for Emergency Doctors, S## for Specialists, E## for Engineers
-- Default password: password123 (in production, use hashed passwords)
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

-- EMERGENCY DOCTORS (URGENCE) - Day shift (8AM - 4PM)
('D01', 'password123', 'Dr. Robert Chen', 'robert.chen@hospital.com', '555-0201', 'EMERGENCY_DOCTOR', 1, '08:00:00', '16:00:00'),

-- EMERGENCY DOCTORS (URGENCE) - Evening shift (4PM - 12AM)
('D02', 'password123', 'Dr. Maria Rodriguez', 'maria.rodriguez@hospital.com', '555-0202', 'EMERGENCY_DOCTOR', 2, '16:00:00', '00:00:00'),
('D03', 'password123', 'Dr. James Wilson', 'james.wilson@hospital.com', '555-0203', 'EMERGENCY_DOCTOR', 2, '16:00:00', '00:00:00'),

-- EMERGENCY DOCTORS (URGENCE) - Night shift (12AM - 8AM)
('D04', 'password123', 'Dr. Amanda Lee', 'amanda.lee@hospital.com', '555-0204', 'EMERGENCY_DOCTOR', 3, '00:00:00', '08:00:00'),

-- CARDIOLOGIST - Day shift (8AM - 4PM)
('S01', 'password123', 'Dr. Michael Thompson', 'michael.thompson@hospital.com', '555-0301', 'CARDIOLOGIST', 1, '08:00:00', '16:00:00'),
('S02', 'password123', 'Dr. Jennifer Adams', 'jennifer.adams@hospital.com', '555-0302', 'CARDIOLOGIST', 1, '08:00:00', '16:00:00'),

-- PULMONOLOGIST - Day shift (8AM - 4PM)
('S03', 'password123', 'Dr. Daniel Kim', 'daniel.kim@hospital.com', '555-0303', 'PULMONOLOGIST', 1, '08:00:00', '16:00:00'),

-- NEUROLOGIST - Day shift (8AM - 4PM)
('S04', 'password123', 'Dr. Patricia Brown', 'patricia.brown@hospital.com', '555-0304', 'NEUROLOGIST', 1, '08:00:00', '16:00:00'),
('S05', 'password123', 'Dr. Ahmed Hassan', 'ahmed.hassan@hospital.com', '555-0305', 'NEUROLOGIST', 1, '08:00:00', '16:00:00'),

-- SURGEON - Day shift (8AM - 4PM)
('S06', 'password123', 'Dr. Susan Miller', 'susan.miller@hospital.com', '555-0306', 'SURGEON', 1, '08:00:00', '16:00:00'),

-- SURGEON - Evening shift (4PM - 12AM)
('S07', 'password123', 'Dr. David Cohen', 'david.cohen@hospital.com', '555-0307', 'SURGEON', 2, '16:00:00', '00:00:00'),

-- OBSTETRICIAN - Day shift (8AM - 4PM)
('S08', 'password123', 'Dr. Laura Martinez', 'laura.martinez@hospital.com', '555-0308', 'OBSTETRICIAN', 1, '08:00:00', '16:00:00'),

-- OBSTETRICIAN - Evening shift (4PM - 12AM)
('S09', 'password123', 'Dr. Kevin Nguyen', 'kevin.nguyen@hospital.com', '555-0309', 'OBSTETRICIAN', 2, '16:00:00', '00:00:00'),

-- PSYCHIATRIST - Day shift (8AM - 4PM)
('S10', 'password123', 'Dr. Elizabeth Taylor', 'elizabeth.taylor@hospital.com', '555-0310', 'PSYCHIATRIST', 1, '08:00:00', '16:00:00'),

-- ENDOCRINOLOGIST - Day shift (8AM - 4PM)
('S11', 'password123', 'Dr. William Garcia', 'william.garcia@hospital.com', '555-0311', 'ENDOCRINOLOGIST', 1, '08:00:00', '16:00:00'),

-- INFECTIOUS_DISEASE - Day shift (8AM - 4PM)
('S12', 'password123', 'Dr. Sophia Anderson', 'sophia.anderson@hospital.com', '555-0312', 'INFECTIOUS_DISEASE', 1, '08:00:00', '16:00:00'),

-- BIOMEDICAL ENGINEERS - Day shift only (8AM - 4PM)
('E01', 'password123', 'Alex Rivera', 'alex.rivera@hospital.com', '555-0401', 'BIOMEDICAL_ENGINEER', 1, '08:00:00', '16:00:00'),
('E02', 'password123', 'Jessica Martinez', 'jessica.martinez@hospital.com', '555-0402', 'BIOMEDICAL_ENGINEER', 1, '08:00:00', '16:00:00')
ON CONFLICT (login) DO NOTHING;
