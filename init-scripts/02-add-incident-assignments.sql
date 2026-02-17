-- ============================================================================
-- Add incident_assignments table for claim functionality
-- This table tracks which employees are assigned to incidents
-- ============================================================================

CREATE TABLE IF NOT EXISTS incident_assignments (
    assignment_id SERIAL PRIMARY KEY,
    incident_id VARCHAR(50) REFERENCES incidents(incident_id),
    employee_id INTEGER REFERENCES employees(employee_id),
    employee_name VARCHAR(100),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_primary BOOLEAN DEFAULT FALSE,
    UNIQUE(incident_id, employee_id)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_incident_assignments_incident ON incident_assignments(incident_id);
CREATE INDEX IF NOT EXISTS idx_incident_assignments_employee ON incident_assignments(employee_id);

-- Populate with existing assignments from incidents table
INSERT INTO incident_assignments (incident_id, employee_id, employee_name, assigned_at, is_primary)
SELECT
    incident_id,
    assigned_employee_id,
    assigned_to,
    assigned_at,
    TRUE
FROM incidents
WHERE assigned_employee_id IS NOT NULL
ON CONFLICT (incident_id, employee_id) DO NOTHING;

COMMIT;
