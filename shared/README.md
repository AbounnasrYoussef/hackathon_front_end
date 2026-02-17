# Patient Care Escalation Platform - Database Setup

## Setup Order

Run the SQL files in this order:

### 1. Create Tables (Schema)
```bash
sudo -u postgres psql -d hospital -f /home/mouerchi/patient-care-platform/shared/schema.sql
```

### 2. Populate Reference Data (Patients, Rooms, Alert Types)
```bash
sudo -u postgres psql -d hospital -f /home/mouerchi/patient-care-platform/shared/reference_data.sql
```

### 3. Populate Employees
```bash
sudo -u postgres psql -d hospital -f /home/mouerchi/patient-care-platform/shared/employees.sql
```

## Database Structure

### Reference Data Tables

**Patients Table:**
- 8 mock patients with realistic data
- Includes: patient_id, name, DOB, gender, room, admission date, status
- Status: ADMITTED or CRITICAL

**Rooms Table:**
- 8 hospital rooms across different floors
- Room types: ICU, GENERAL, EMERGENCY, MATERNITY
- Tracks occupancy and current patient assignment

**Alert Type Definitions Table:**
- 33 comprehensive hospital alert types
- Categories: CARDIAC, RESPIRATORY, NEUROLOGICAL, TRAUMA, METABOLIC, INFECTION, MEDICATION, EQUIPMENT, SAFETY, OBSTETRIC, PSYCHIATRIC
- Each alert includes severity, description, and typical values

### Operational Tables

**Employees Table:**
- 26 staff members across 10 specialized roles
- Login-based authentication system
- Shift tracking (Day, Evening, Night)

**Alerts Table:**
- Stores all generated patient alerts
- Links to patients and alert type definitions

**Incidents Table:**
- Created automatically from alerts
- Tracks lifecycle: OPEN → ASSIGNED → ACKNOWLEDGED → RESOLVED

## Sample Data

### Patients
- P4521 (John Smith) - Room 312, ICU, CRITICAL
- P2103 (Sarah Johnson) - Room 205, General, ADMITTED
- P7788 (Michael Chen) - Room 401, General, ADMITTED
- P3344 (Emma Williams) - Room 108, Emergency, CRITICAL
- P5566 (David Brown) - Room 523, ICU, CRITICAL
- P8899 (Lisa Garcia) - Room 614, Maternity, ADMITTED
- P1122 (James Martinez) - Room 307, General, ADMITTED
- P6677 (Maria Rodriguez) - Room 501, General, ADMITTED

### Employees (26 staff across 10 roles)
**Nurses (6):** N01-N06 (all shifts)  
**Emergency Doctors (4):** D01-D04 (all shifts)  
**Cardiologists (2):** S01-S02 (day shift)  
**Pulmonologist (1):** S03 (day shift)  
**Neurologists (2):** S04-S05 (day shift)  
**Surgeons (2):** S06-S07 (day/evening)  
**Obstetricians (2):** S08-S09 (day/evening)  
**Psychiatrist (1):** S10 (day shift)  
**Endocrinologist (1):** S11 (day shift)  
**Infectious Disease (1):** S12 (day shift)  
**Biomedical Engineers (2):** E01-E02 (day shift)

Default password for all: `password123`

## Adding New Data

### Add a Patient
```sql
INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, gender, room, status) 
VALUES ('P9999', 'John', 'Doe', '1980-01-01', 'M', '999', 'ADMITTED');
```

### Add an Alert Type
```sql
INSERT INTO alert_type_definitions (alert_type, severity, category, description, typical_values)
VALUES ('NEW_ALERT_TYPE', 'HIGH', 'CATEGORY', 'Description here', 
        ARRAY['Value 1', 'Value 2', 'Value 3']);
```

### Add an Employee
```sql
INSERT INTO employees (login, password, name, email, phone, role, tier, shift_start_time, shift_end_time) 
VALUES ('N99', 'password123', 'New Nurse', 'nurse@hospital.com', '555-9999', 'NURSE', 1, '08:00:00', '16:00:00');
```

## Viewing Data

### View all patients with room assignments
```bash
sudo -u postgres psql -d hospital -c "SELECT patient_id, first_name, last_name, room, status FROM patients ORDER BY room;"
```

### View all alert types
```bash
sudo -u postgres psql -d hospital -c "SELECT alert_type, severity, category FROM alert_type_definitions ORDER BY category, severity;"
```

### View employees by role
```bash
sudo -u postgres psql -d hospital -c "SELECT login, name, role, tier, shift_start_time, shift_end_time FROM employees ORDER BY role, tier;"
```

### View logged-in employees
```bash
sudo -u postgres psql -d hospital -c "SELECT login, name, role, is_logged_in, last_login FROM employees WHERE is_logged_in = TRUE;"
```
