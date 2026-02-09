from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import pika
import os
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
import json
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hospital')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
ONCALL_SERVICE_URL = os.getenv('ONCALL_SERVICE_URL', 'http://localhost:8003')

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

def get_db_connection():
    """Get database connection with retry logic."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Error: Database connection failed: {e}")
        return None

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
        conn.close()
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
        conn.close()
        
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

def auto_assign_incident(incident_id, alert_type):
    """Automatically assign incident to available on-call staff based on alert type."""
    try:
        # Get priority role list for this alert type
        role_priorities = ALERT_ROLE_MAPPING.get(alert_type, ['NURSE'])
        
        for role in role_priorities:
            # Query oncall service for available staff with this role
            response = requests.get(
                f"{ONCALL_SERVICE_URL}/oncall/current",
                params={'role': role},
                timeout=5
            )
            
            if response.status_code == 200:
                available_staff = response.json()
                if available_staff and len(available_staff) > 0:
                    # Use tier 1 priority (lowest tier number)
                    staff = min(available_staff, key=lambda x: x['tier'])
                    
                    # Assign incident to this staff member
                    assign_response = requests.post(
                        f"{ONCALL_SERVICE_URL}/oncall/assign",
                        json={
                            'incident_id': incident_id,
                            'employee_id': staff['employee_id']
                        },
                        timeout=5
                    )
                    
                    if assign_response.status_code == 200:
                        assignment_data = assign_response.json()
                        incident_data = assignment_data.get('incident', {})
                        severity = incident_data.get('severity', 'MEDIUM')
                        patient_id = incident_data.get('patient_id', 'Unknown')
                        
                        print(f"✅ Auto-assigned incident {incident_id} to {staff['name']} ({role})")
                        
                        # Add to history
                        add_to_history(
                            incident_id,
                            staff['employee_id'],
                            staff['name'],
                            'ASSIGNED',
                            'OPEN',
                            'ASSIGNED',
                            f"Auto-assigned based on alert type: {alert_type}"
                        )
                        
                        # 🆕 Send notification via RabbitMQ
                        notification_data = {
                            'type': 'INCIDENT_ASSIGNED',
                            'employee_id': staff['employee_id'],
                            'employee_name': staff['name'],
                            'employee_email': staff.get('email', ''),
                            'employee_phone': staff.get('phone', ''),
                            'incident_id': incident_id,
                            'alert_type': alert_type,
                            'severity': severity,
                            'patient_id': patient_id,
                            'title': f'New {severity} Incident Assigned',
                            'message': f'{alert_type} incident for patient {patient_id} has been assigned to you.',
                            'data': {
                                'incident_id': incident_id,
                                'alert_type': alert_type,
                                'role': role,
                                'tier': staff['tier']
                            },
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        publish_notification(notification_data)
                        
                        return True
        
        print(f"⚠️  No available staff found for incident {incident_id} (alert type: {alert_type})")
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
            INSERT INTO incidents (incident_id, alert_id, patient_id, status, severity, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            incident_id,
            alert_data['alert_id'],
            alert_data['patient_id'],
            'OPEN',
            alert_data['severity'],
            datetime.now()
        ))
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Created incident: {incident_id} from alert {alert_data['alert_id']}")
        
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
        conn.close()
        
        return jsonify(incidents), 200
        
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
        conn.close()
        
        return jsonify({
            'incident': incident,
            'history': history
        }), 200
        
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
        
        # Calculate response time
        calculate_time_metrics(incident_id)
        
        # Mark notification as read
        try:
            notification_response = requests.patch(
                f"http://localhost:8004/notifications/incident/{incident_id}/mark-read",
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
        conn.close()
        
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
            'STATUS_CHANGED',
            'ACKNOWLEDGED',
            'IN_PROGRESS',
            note
        )
        
        # Get updated incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        updated_incident = cur.fetchone()
        
        cur.close()
        conn.close()
        
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
        conn.close()
        
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
            'RESOLVED',
            incident['status'],
            'RESOLVED',
            resolution_notes
        )
        
        # Calculate all time metrics
        calculate_time_metrics(incident_id)
        
        # Get updated incident with metrics
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        updated_incident = cur.fetchone()
        
        cur.close()
        conn.close()
        
        return jsonify(updated_incident), 200
        
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
        conn.close()
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002, debug=False)
