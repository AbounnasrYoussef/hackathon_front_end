from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
import pika
import os
import time
import threading
import random
from datetime import datetime
from dotenv import load_dotenv
import json
import requests
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

load_dotenv()

app = Flask(__name__)
CORS(app)

# Prometheus Metrics
incidents_total = Counter('incidents_total', 'Total incidents created', ['severity'])
incident_mtta_seconds = Histogram('incident_mtta_seconds', 'Mean Time To Acknowledge', buckets=[5, 10, 30, 60, 300, 600])
incident_mttr_seconds = Histogram('incident_mttr_seconds', 'Mean Time To Resolve', buckets=[60, 300, 600, 1800, 3600, 7200])

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hospital')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
ONCALL_SERVICE_URL = os.getenv('ONCALL_SERVICE_URL', 'http://localhost:8003')
NOTIFICATION_SERVICE_URL = os.getenv('NOTIFICATION_SERVICE_URL', 'http://notification-service:8004')

# Alert type to role mapping with priority order
ALERT_ROLE_MAPPING = {
    # CARDIAC/CARDIOVASCULAR
    'CARDIAC_ARREST': ['EMERGENCY_DOCTOR', 'CARDIOLOGIST'],
    'CARDIAC_ABNORMAL': ['EMERGENCY_DOCTOR', 'CARDIOLOGIST'],
    'MYOCARDIAL_INFARCTION': ['EMERGENCY_DOCTOR', 'CARDIOLOGIST'],
    
    # RESPIRATORY
    'RESPIRATORY_DISTRESS': ['EMERGENCY_DOCTOR', 'PULMONOLOGIST', 'NURSE'],
    'O2_SATURATION_LOW': ['NURSE', 'EMERGENCY_DOCTOR', 'PULMONOLOGIST'],
    'APNEA_DETECTED': ['EMERGENCY_DOCTOR', 'NURSE'],
    'VENTILATOR_ALARM': ['NURSE', 'EMERGENCY_DOCTOR', 'PULMONOLOGIST'],
    
    # NEUROLOGICAL
    'STROKE_SUSPECTED': ['EMERGENCY_DOCTOR', 'NEUROLOGIST'],
    'SEIZURE_DETECTED': ['NURSE', 'EMERGENCY_DOCTOR', 'NEUROLOGIST'],
    'INTRACRANIAL_PRESSURE_HIGH': ['EMERGENCY_DOCTOR', 'NEUROLOGIST'],
    
    # BLOOD PRESSURE
    'HYPERTENSION_CRISIS': ['NURSE', 'EMERGENCY_DOCTOR'],
    'HYPOTENSION_SEVERE': ['NURSE', 'EMERGENCY_DOCTOR'],
    
    # BLEEDING/TRAUMA
    'HEMORRHAGE_MAJOR': ['EMERGENCY_DOCTOR', 'SURGEON'],
    'TRAUMA_SEVERE': ['EMERGENCY_DOCTOR', 'SURGEON'],
    
    # GLUCOSE/METABOLIC
    'HYPOGLYCEMIA_SEVERE': ['NURSE', 'EMERGENCY_DOCTOR'],
    'HYPERGLYCEMIA_SEVERE': ['NURSE', 'EMERGENCY_DOCTOR'],
    'DIABETIC_KETOACIDOSIS': ['EMERGENCY_DOCTOR', 'ENDOCRINOLOGIST'],
    
    # INFECTION/SEPSIS
    'SEPSIS_SUSPECTED': ['EMERGENCY_DOCTOR', 'INFECTIOUS_DISEASE'],
    'FEVER_HIGH': ['NURSE'],
    
    # MEDICATION/TREATMENT
    'MEDICATION_DELAYED': ['NURSE'],
    'MEDICATION_ERROR': ['NURSE', 'EMERGENCY_DOCTOR'],
    'ADVERSE_REACTION': ['NURSE', 'EMERGENCY_DOCTOR'],
    'IV_INFILTRATION': ['NURSE'],
    
    # EQUIPMENT/TECHNICAL
    'EQUIPMENT_MALFUNCTION': ['BIOMEDICAL_ENGINEER', 'NURSE'],
    'EQUIPMENT_LOW_BATTERY': ['BIOMEDICAL_ENGINEER', 'NURSE'],
    
    # PATIENT SAFETY
    'FALL_DETECTED': ['NURSE', 'EMERGENCY_DOCTOR'],
    'BED_EXIT_UNAUTHORIZED': ['NURSE'],
    'RESTRAINT_ALERT': ['NURSE', 'EMERGENCY_DOCTOR'],
    
    # OBSTETRIC
    'FETAL_DISTRESS': ['EMERGENCY_DOCTOR', 'OBSTETRICIAN'],
    'LABOR_COMPLICATIONS': ['NURSE', 'OBSTETRICIAN'],
    
    # PSYCHIATRIC
    'AGITATION_SEVERE': ['NURSE', 'EMERGENCY_DOCTOR', 'PSYCHIATRIST'],
    'SUICIDE_RISK': ['PSYCHIATRIST', 'NURSE', 'EMERGENCY_DOCTOR']
}

# Connection pool (initialized lazily)
db_pool = None

def init_db_pool():
    """Initialize the database connection pool."""
    global db_pool
    if db_pool is None:
        try:
            db_pool = ThreadedConnectionPool(2, 10, DATABASE_URL)
            print("✅ Database connection pool initialized")
        except Exception as e:
            print(f"❌ Error: Failed to initialize connection pool: {e}")

def get_db_connection():
    """Get database connection from pool."""
    global db_pool
    try:
        if db_pool is None:
            init_db_pool()
        if db_pool:
            return db_pool.getconn()
        return None
    except Exception as e:
        print(f"❌ Error: Database connection failed: {e}")
        return None

def return_db_connection(conn):
    """Return a connection to the pool."""
    if db_pool and conn:
        db_pool.putconn(conn)

def add_to_history(incident_id, employee_id, employee_name, action, previous_status=None, new_status=None, note=None):
    """Add entry to incident history for audit trail."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incident_history (incident_id, employee_id, employee_name, action, previous_status, new_status, note, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (incident_id, employee_id, employee_name, action, previous_status, new_status, note, datetime.now()))
        
        conn.commit()
        cur.close()
        return_db_connection(conn)
        return True
    except Exception as e:
        print(f"❌ Error adding to history: {e}")
        return False

def calculate_time_metrics(incident_id):
    """Calculate and update time metrics for an incident."""
    try:
        conn = get_db_connection()
        if not conn:
            return
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        incident = cur.fetchone()
        
        if not incident:
            return
        
        response_time = None
        resolution_time = None
        total_time = None
        
        # Calculate response time (OPEN → ACKNOWLEDGED)
        if incident['acknowledged_at'] and incident['created_at']:
            response_time = (incident['acknowledged_at'] - incident['created_at']).total_seconds()
        
        # Calculate resolution time (ACKNOWLEDGED → RESOLVED)
        if incident['resolved_at'] and incident['acknowledged_at']:
            resolution_time = (incident['resolved_at'] - incident['acknowledged_at']).total_seconds()
        
        # Calculate total time (OPEN → RESOLVED)
        if incident['resolved_at'] and incident['created_at']:
            total_time = (incident['resolved_at'] - incident['created_at']).total_seconds()
        
        # Update metrics
        cur.execute("""
            UPDATE incidents 
            SET response_time_seconds = %s,
                resolution_time_seconds = %s,
                total_time_seconds = %s
            WHERE incident_id = %s
        """, (response_time, resolution_time, total_time, incident_id))
        
        conn.commit()
        cur.close()
        return_db_connection(conn)
        
    except Exception as e:
        print(f"❌ Error calculating time metrics: {e}")

def publish_notification(notification_data):
    """Publish notification request to RabbitMQ notifications queue."""
    try:
        connection = get_rabbitmq_connection()
        if not connection:
            print("❌ Failed to publish notification: No RabbitMQ connection")
            return False
        
        channel = connection.channel()
        channel.queue_declare(queue='notifications', durable=True)
        
        message = json.dumps(notification_data, default=str)
        channel.basic_publish(
            exchange='',
            routing_key='notifications',
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        connection.close()
        print(f"✅ Notification published to queue for employee {notification_data.get('employee_id')}")
        return True
        
    except Exception as e:
        print(f"❌ Error publishing notification: {e}")
        return False

def get_staff_workload(employee_id):
    """Get current workload for a staff member."""
    try:
        conn = get_db_connection()
        if not conn:
            return {'total': 999, 'in_progress': 999}
        
        cur = conn.cursor()
        
        # Count total active incidents
        cur.execute("""
            SELECT COUNT(*) FROM incidents 
            WHERE assigned_employee_id = %s AND status != 'RESOLVED'
        """, (employee_id,))
        total_active = cur.fetchone()[0]
        
        # Count in-progress incidents
        cur.execute("""
            SELECT COUNT(*) FROM incidents 
            WHERE assigned_employee_id = %s AND status = 'IN_PROGRESS'
        """, (employee_id,))
        in_progress = cur.fetchone()[0]
        
        cur.close()
        return_db_connection(conn)
        
        return {'total': total_active, 'in_progress': in_progress}
    except Exception as e:
        print(f"❌ Error getting workload: {e}")
        return {'total': 999, 'in_progress': 999}

def assign_incident_to_staff(incident_id, staff, alert_type, role, workload):
    """Assign an incident to a specific staff member."""
    conn = get_db_connection()
    if not conn:
        return False
    cur = conn.cursor()

    cur.execute("""
        UPDATE incidents
        SET assigned_to = %s, assigned_employee_id = %s, assigned_at = %s, status = 'ASSIGNED'
        WHERE incident_id = %s
    """, (staff['name'], staff['employee_id'], datetime.now(), incident_id))

    cur.execute("""
        INSERT INTO incident_assignments (incident_id, employee_id, employee_name, is_primary)
        VALUES (%s, %s, %s, TRUE)
        ON CONFLICT (incident_id, employee_id) DO NOTHING
    """, (incident_id, staff['employee_id'], staff['name']))

    conn.commit()
    cur.close()
    return_db_connection(conn)

    print(f"✅ Assigned {incident_id} to {staff['name']} ({role}) [Workload: {workload['in_progress']} in-progress, {workload['total']} total]")

    add_to_history(incident_id, staff['employee_id'], staff['name'], 'ASSIGNED', 'OPEN', 'ASSIGNED',
                   f"Auto-assigned to {role} (least busy: {workload['total']} active incidents)")

    publish_notification({
        'type': 'INCIDENT_ASSIGNED',
        'employee_id': staff['employee_id'],
        'employee_name': staff['name'],
        'employee_email': staff.get('email', ''),
        'employee_phone': staff.get('phone', ''),
        'incident_id': incident_id,
        'alert_type': alert_type,
        'severity': 'MEDIUM',
        'patient_id': 'Unknown',
        'title': 'New Incident Assigned',
        'message': f'{alert_type} incident assigned to you.',
        'data': {'incident_id': incident_id, 'alert_type': alert_type, 'role': role},
        'timestamp': datetime.now().isoformat()
    })
    return True

def pick_least_busy_staff(available_staff, role_label):
    """Pick the staff member with the least workload from a list."""
    staff_with_workload = []
    print(f"📊 Checking workload for {len(available_staff)} {role_label} staff members...")
    for staff in available_staff:
        workload = get_staff_workload(staff['employee_id'])
        staff_with_workload.append({'staff': staff, 'workload': workload})
        print(f"   {staff['name']} (ID:{staff['employee_id']}): {workload['in_progress']} in-progress, {workload['total']} total")

    staff_with_workload.sort(key=lambda x: (x['workload']['in_progress'], x['workload']['total']))
    selected = staff_with_workload[0]
    print(f"   → Selected: {selected['staff']['name']} (least busy)")
    return selected['staff'], selected['workload']

def auto_assign_incident(incident_id, alert_type):
    """Assign incident using smart load-balancing strategy based on current workload."""
    try:
        role_priorities = ALERT_ROLE_MAPPING.get(alert_type, ['NURSE'])

        # Step 1: Try to find logged-in staff for each specific role
        for role in role_priorities:
            try:
                response = requests.get(
                    f"{ONCALL_SERVICE_URL}/oncall/current",
                    params={'role': role},
                    timeout=5
                )

                if response.status_code == 200:
                    available_staff = response.json()
                    if available_staff and len(available_staff) > 0:
                        staff, workload = pick_least_busy_staff(available_staff, role)
                        return assign_incident_to_staff(incident_id, staff, alert_type, role, workload)
            except Exception as e:
                print(f"⚠️  Error checking role {role}: {e}")
                continue

        # Step 2: Fallback - try ANY logged-in employee regardless of role
        print(f"⚠️  No specific role match for {alert_type}, trying any logged-in employee...")
        try:
            response = requests.get(
                f"{ONCALL_SERVICE_URL}/oncall/schedules",
                timeout=5
            )
            if response.status_code == 200:
                all_employees = response.json()
                logged_in = [e for e in all_employees if e.get('is_logged_in')]
                if logged_in:
                    staff, workload = pick_least_busy_staff(logged_in, 'ANY_ROLE')
                    return assign_incident_to_staff(incident_id, staff, alert_type, staff.get('role', 'UNKNOWN'), workload)
        except Exception as e:
            print(f"⚠️  Error in fallback assignment: {e}")

        print(f"⚠️  No available staff for {incident_id} (alert: {alert_type}, tried: {role_priorities} + fallback)")
        return False

    except Exception as e:
        print(f"❌ Error: Auto-assignment failed for incident {incident_id}: {e}")
        return False

def create_incident_from_alert(alert_data):
    """Create an incident from an alert."""
    try:
        incident_id = f"INC-{int(time.time() * 1000)}"
        
        conn = get_db_connection()
        if not conn:
            return None
            
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO incidents (incident_id, alert_id, patient_id, room, alert_type, status, severity, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            incident_id,
            alert_data['alert_id'],
            alert_data['patient_id'],
            alert_data.get('room'),
            alert_data.get('alert_type'),
            'OPEN',
            alert_data['severity'],
            datetime.now()
        ))
        conn.commit()
        cur.close()
        return_db_connection(conn)
        
        print(f"✅ Created incident: {incident_id} from alert {alert_data['alert_id']}")

        # Update Prometheus metrics
        incidents_total.labels(severity=alert_data['severity']).inc()

        # Add to history
        add_to_history(incident_id, None, 'SYSTEM', 'CREATED', None, 'OPEN', f"Created from alert {alert_data['alert_id']}")
        
        # Auto-assign incident based on alert type
        auto_assign_incident(incident_id, alert_data['alert_type'])
        
        return incident_id
        
    except Exception as e:
        print(f"❌ Error: Failed to create incident: {e}")
        return None

def process_alert_message(ch, method, properties, body):
    """Callback function to process alerts from RabbitMQ."""
    try:
        alert_data = json.loads(body)
        create_incident_from_alert(alert_data)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"❌ Error: Failed to process alert message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def get_rabbitmq_connection():
    """Get RabbitMQ connection with retry logic."""
    for attempt in range(5):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=RABBITMQ_HOST)
            )
            return connection
        except Exception as e:
            print(f"❌ Error: RabbitMQ connection attempt {attempt + 1}/5 failed: {e}")
            if attempt < 4:
                time.sleep(5)
    return None

def rabbitmq_consumer_thread():
    """Background thread that listens to RabbitMQ alerts queue."""
    print("🚀 RabbitMQ consumer thread started")
    while True:
        try:
            connection = get_rabbitmq_connection()
            if not connection:
                print("❌ Error: Could not establish RabbitMQ connection, retrying in 10s...")
                time.sleep(10)
                continue
                
            channel = connection.channel()
            channel.queue_declare(queue='alerts', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='alerts', on_message_callback=process_alert_message)
            
            print("✅ Listening for alerts on RabbitMQ queue 'alerts'")
            channel.start_consuming()
            
        except Exception as e:
            print(f"❌ Error: RabbitMQ consumer error: {e}")
            time.sleep(10)

# Start background thread
consumer_thread = threading.Thread(target=rabbitmq_consumer_thread, daemon=True)
consumer_thread.start()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'incident-service'}), 200

@app.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/incidents', methods=['GET'])
def get_incidents():
    """Get all incidents with optional status filter."""
    try:
        status_filter = request.args.get('status')

        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor(cursor_factory=RealDictCursor)

        if status_filter:
            cur.execute("SELECT * FROM incidents WHERE status = %s ORDER BY created_at DESC", (status_filter,))
        else:
            cur.execute("SELECT * FROM incidents ORDER BY created_at DESC")

        incidents = cur.fetchall()
        cur.close()
        return_db_connection(conn)

        return jsonify(incidents), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/incidents/metrics', methods=['GET'])
def get_metrics():
    """Get performance metrics."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500

        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Average times
        cur.execute("""
            SELECT
                AVG(response_time_seconds) as avg_response_time,
                AVG(resolution_time_seconds) as avg_resolution_time,
                AVG(total_time_seconds) as avg_total_time
            FROM incidents
            WHERE status = 'RESOLVED'
        """)
        times = cur.fetchone()

        # Count by severity
        cur.execute("""
            SELECT severity, COUNT(*) as count
            FROM incidents
            GROUP BY severity
        """)
        severity_counts = {row['severity']: row['count'] for row in cur.fetchall()}

        # Count by status
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM incidents
            GROUP BY status
        """)
        status_counts = {row['status']: row['count'] for row in cur.fetchall()}

        # Employee performance
        cur.execute("""
            SELECT
                e.name,
                e.role,
                COUNT(i.incident_id) as incidents_handled,
                AVG(i.response_time_seconds) as avg_response_seconds,
                AVG(i.resolution_time_seconds) as avg_resolution_seconds
            FROM incidents i
            JOIN employees e ON i.resolved_by_employee_id = e.employee_id
            WHERE i.status = 'RESOLVED'
            GROUP BY e.employee_id, e.name, e.role
            ORDER BY avg_response_seconds ASC
        """)
        employee_performance = cur.fetchall()

        cur.close()
        return_db_connection(conn)

        metrics = {
            'average_times': {
                'response_time_seconds': float(times['avg_response_time']) if times['avg_response_time'] else 0,
                'response_time_minutes': float(times['avg_response_time']) / 60 if times['avg_response_time'] else 0,
                'resolution_time_seconds': float(times['avg_resolution_time']) if times['avg_resolution_time'] else 0,
                'resolution_time_minutes': float(times['avg_resolution_time']) / 60 if times['avg_resolution_time'] else 0,
                'total_time_seconds': float(times['avg_total_time']) if times['avg_total_time'] else 0,
                'total_time_minutes': float(times['avg_total_time']) / 60 if times['avg_total_time'] else 0
            },
            'severity_counts': severity_counts,
            'status_counts': status_counts,
            'employee_performance': employee_performance
        }

        return jsonify(metrics), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/incidents/<incident_id>', methods=['GET'])
def get_incident(incident_id):
    """Get specific incident details with history."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        incident = cur.fetchone()
        
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        # Get history
        cur.execute("""
            SELECT * FROM incident_history 
            WHERE incident_id = %s 
            ORDER BY timestamp ASC
        """, (incident_id,))
        history = cur.fetchall()
        
        cur.close()
        return_db_connection(conn)
        
        return jsonify({
            'incident': incident,
            'history': history
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/incidents/<incident_id>/claim', methods=['PATCH'])
def claim_incident(incident_id):
    """Allow any staff member to claim/take an incident even if not originally assigned to them."""
    try:
        data = request.get_json() or {}
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name')
        
        if not employee_id or not employee_name:
            return jsonify({'error': 'employee_id and employee_name are required'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        incident = cur.fetchone()
        
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        # Can only claim if incident is OPEN, ASSIGNED, or ACKNOWLEDGED (not already in progress or resolved)
        if incident['status'] not in ['OPEN', 'ASSIGNED', 'ACKNOWLEDGED']:
            return jsonify({'error': f'Cannot claim incident with status {incident["status"]}. Only OPEN, ASSIGNED, or ACKNOWLEDGED incidents can be claimed.'}), 400
        
        previous_assignee = incident.get('assigned_to', 'Unassigned')
        previous_status = incident['status']
        
        # Update incident assignment
        cur.execute("""
            UPDATE incidents 
            SET assigned_to = %s,
                assigned_employee_id = %s,
                assigned_at = %s,
                status = 'ACKNOWLEDGED'
            WHERE incident_id = %s
        """, (employee_name, employee_id, datetime.now(), incident_id))
        
        # Update or insert into incident_assignments
        cur.execute("""
            INSERT INTO incident_assignments (incident_id, employee_id, employee_name, is_primary)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (incident_id, employee_id) 
            DO UPDATE SET is_primary = TRUE, assigned_at = NOW()
        """, (incident_id, employee_id, employee_name))
        
        conn.commit()
        
        print(f"✅ Incident {incident_id} claimed by {employee_name} (was: {previous_assignee})")
        
        # Add to history
        if previous_assignee == 'Unassigned' or previous_assignee is None:
            note = f"Claimed unassigned incident"
        else:
            note = f"Claimed incident (previously assigned to {previous_assignee})"
        
        add_to_history(
            incident_id,
            employee_id,
            employee_name,
            'CLAIMED',
            previous_status,
            'ACKNOWLEDGED',
            note
        )
        
        # Send notification to previous assignee if there was one
        if incident.get('assigned_employee_id') and incident['assigned_employee_id'] != employee_id:
            try:
                publish_notification({
                    'type': 'INCIDENT_REASSIGNED',
                    'employee_id': incident['assigned_employee_id'],
                    'employee_name': incident['assigned_to'],
                    'incident_id': incident_id,
                    'title': 'Incident Claimed by Another Staff Member',
                    'message': f'{employee_name} has claimed incident {incident_id}',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"⚠️ Could not notify previous assignee: {e}")
        
        # Get updated incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        updated_incident = cur.fetchone()
        
        cur.close()
        return_db_connection(conn)
        
        return jsonify(updated_incident), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/incidents/<incident_id>/acknowledge', methods=['PATCH'])
def acknowledge_incident(incident_id):
    """Employee acknowledges they've seen the incident (ASSIGNED → ACKNOWLEDGED)."""
    try:
        data = request.get_json() or {}
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        incident = cur.fetchone()
        
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        if incident['status'] not in ['ASSIGNED', 'OPEN']:
            return jsonify({'error': f'Cannot acknowledge incident with status {incident["status"]}'}), 400
        
        # Update to ACKNOWLEDGED
        acknowledged_at = datetime.now()
        cur.execute("""
            UPDATE incidents 
            SET status = 'ACKNOWLEDGED',
                acknowledged_at = %s
            WHERE incident_id = %s
        """, (acknowledged_at, incident_id))
        
        conn.commit()
        
        print(f"✅ Incident {incident_id} acknowledged by {employee_name}")
        
        # Add to history
        add_to_history(
            incident_id,
            employee_id,
            employee_name,
            'ACKNOWLEDGED',
            incident['status'],
            'ACKNOWLEDGED',
            'Employee acknowledged the incident'
        )
        
        # Calculate response time and record MTTA in Prometheus
        calculate_time_metrics(incident_id)
        if incident['created_at']:
            mtta_seconds = (acknowledged_at - incident['created_at']).total_seconds()
            incident_mtta_seconds.observe(mtta_seconds)

        # Mark notification as read
        try:
            notification_response = requests.patch(
                f"{NOTIFICATION_SERVICE_URL}/notifications/incident/{incident_id}/mark-read",
                json={'employee_id': employee_id},
                timeout=3
            )
            if notification_response.status_code == 200:
                print(f"✅ Notification marked as read for incident {incident_id}")
        except Exception as e:
            print(f"⚠️ Could not mark notification as read: {e}")
        
        # Get updated incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        updated_incident = cur.fetchone()
        
        cur.close()
        return_db_connection(conn)
        
        return jsonify(updated_incident), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/incidents/<incident_id>/start', methods=['PATCH'])
def start_incident(incident_id):
    """Employee starts working on incident (ACKNOWLEDGED → IN_PROGRESS)."""
    try:
        data = request.get_json() or {}
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name')
        note = data.get('note', 'Started working on incident')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        incident = cur.fetchone()
        
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        if incident['status'] != 'ACKNOWLEDGED':
            return jsonify({'error': f'Cannot start incident with status {incident["status"]}. Must be ACKNOWLEDGED first.'}), 400
        
        # Update to IN_PROGRESS
        in_progress_at = datetime.now()
        cur.execute("""
            UPDATE incidents 
            SET status = 'IN_PROGRESS',
                in_progress_at = %s
            WHERE incident_id = %s
        """, (in_progress_at, incident_id))
        
        conn.commit()
        
        print(f"✅ Incident {incident_id} started by {employee_name}")
        
        # Add to history
        add_to_history(
            incident_id,
            employee_id,
            employee_name,
            'STARTED_PROGRESS',
            'ACKNOWLEDGED',
            'IN_PROGRESS',
            note
        )
        
        # Get updated incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        updated_incident = cur.fetchone()
        
        cur.close()
        return_db_connection(conn)
        
        return jsonify(updated_incident), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/incidents/<incident_id>/notes', methods=['POST'])
def add_note(incident_id):
    """Add progress note during incident handling."""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name')
        note = data.get('note')
        
        if not note or len(note.strip()) == 0:
            return jsonify({'error': 'Note cannot be empty'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        incident = cur.fetchone()
        
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        # Append note to intermediate_notes array
        cur.execute("""
            UPDATE incidents 
            SET intermediate_notes = array_append(COALESCE(intermediate_notes, ARRAY[]::TEXT[]), %s)
            WHERE incident_id = %s
        """, (f"[{datetime.now().strftime('%H:%M:%S')}] {note}", incident_id))
        
        conn.commit()
        
        print(f"✅ Note added to incident {incident_id} by {employee_name}")
        
        # Add to history
        add_to_history(
            incident_id,
            employee_id,
            employee_name,
            'NOTE_ADDED',
            incident['status'],
            incident['status'],
            note
        )
        
        # Get updated incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        updated_incident = cur.fetchone()
        
        cur.close()
        return_db_connection(conn)
        
        return jsonify(updated_incident), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/incidents/<incident_id>/resolve', methods=['PATCH'])
def resolve_incident(incident_id):
    """Resolve incident with required resolution notes (IN_PROGRESS → RESOLVED)."""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        employee_name = data.get('employee_name')
        resolution_notes = data.get('resolution_notes')
        
        # Validate resolution notes
        if not resolution_notes or len(resolution_notes.strip()) < 10:
            return jsonify({'error': 'Resolution notes are required (minimum 10 characters)'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get current incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        incident = cur.fetchone()
        
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        if incident['status'] == 'RESOLVED':
            return jsonify({'error': 'Incident already resolved'}), 400
        
        # Update to RESOLVED
        resolved_at = datetime.now()
        cur.execute("""
            UPDATE incidents 
            SET status = 'RESOLVED',
                resolved_at = %s,
                resolution_notes = %s,
                resolved_by_employee_id = %s
            WHERE incident_id = %s
        """, (resolved_at, resolution_notes, employee_id, incident_id))
        
        conn.commit()
        
        print(f"✅ Incident {incident_id} resolved by {employee_name}")
        
        # Add to history
        add_to_history(
            incident_id,
            employee_id,
            employee_name,
            'INCIDENT_RESOLVED',
            incident['status'],
            'RESOLVED',
            resolution_notes
        )
        
        # Calculate all time metrics and record MTTR in Prometheus
        calculate_time_metrics(incident_id)
        if incident['created_at']:
            mttr_seconds = (resolved_at - incident['created_at']).total_seconds()
            incident_mttr_seconds.observe(mttr_seconds)

        # Get updated incident with metrics
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        updated_incident = cur.fetchone()
        
        cur.close()
        return_db_connection(conn)
        
        return jsonify(updated_incident), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=False)
