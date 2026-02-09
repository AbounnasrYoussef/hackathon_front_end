from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import pika
import os
import time
import random
import threading
from datetime import datetime
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hospital')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')

# No hardcoded data - all retrieved from database!

def get_db_connection():
    """Get database connection with retry logic."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Error: Database connection failed: {e}")
        return None

def get_random_patient():
    """Get a random admitted patient from database."""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT p.patient_id, p.first_name, p.last_name, p.room, p.status
            FROM patients p
            WHERE p.status IN ('ADMITTED', 'CRITICAL')
            ORDER BY RANDOM()
            LIMIT 1
        """)
        patient = cur.fetchone()
        cur.close()
        conn.close()
        return patient
    except Exception as e:
        print(f"❌ Error: Failed to fetch patient: {e}")
        return None

def get_random_alert_type():
    """Get a random alert type configuration from database."""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT alert_type, severity, typical_values
            FROM alert_type_definitions
            ORDER BY RANDOM()
            LIMIT 1
        """)
        alert_config = cur.fetchone()
        cur.close()
        conn.close()
        return alert_config
    except Exception as e:
        print(f"❌ Error: Failed to fetch alert type: {e}")
        return None

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

def publish_alert_to_queue(alert_data):
    """Publish alert to RabbitMQ queue."""
    try:
        connection = get_rabbitmq_connection()
        if not connection:
            return False
            
        channel = connection.channel()
        channel.queue_declare(queue='alerts', durable=True)
        
        message = json.dumps(alert_data, default=str)
        channel.basic_publish(
            exchange='',
            routing_key='alerts',
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
        )
        
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Error: Failed to publish to RabbitMQ: {e}")
        return False

def generate_alert():
    """Generate a patient alert using real database data."""
    try:
        # Get random patient from database (includes room assignment)
        patient = get_random_patient()
        if not patient:
            print("⚠️  No admitted patients found in database")
            return None
        
        # Get random alert type from database (includes severity and possible values)
        alert_config = get_random_alert_type()
        if not alert_config:
            print("⚠️  No alert types found in database")
            return None
        
        # Generate alert data
        alert_id = f"ALT-{int(time.time() * 1000)}"
        patient_id = patient['patient_id']
        room = patient['room']
        alert_type = alert_config['alert_type']
        severity = alert_config['severity']
        value = random.choice(alert_config['typical_values'])
        created_at = datetime.now()
        
        # Store in database
        conn = get_db_connection()
        if not conn:
            return None
            
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO alerts (alert_id, patient_id, room, alert_type, severity, value, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (alert_id, patient_id, room, alert_type, severity, value, created_at))
        conn.commit()
        cur.close()
        conn.close()
        
        alert_data = {
            'alert_id': alert_id,
            'patient_id': patient_id,
            'room': room,
            'alert_type': alert_type,
            'severity': severity,
            'value': value,
            'created_at': created_at.isoformat()
        }
        
        # Publish to RabbitMQ
        publish_alert_to_queue(alert_data)
        
        print(f"✅ Generated alert: {alert_id} - {alert_type} ({severity}) for patient {patient_id} in room {room}")
        return alert_data
        
    except Exception as e:
        print(f"❌ Error: Failed to generate alert: {e}")
        return None

def alert_generator_thread():
    """Background thread that generates alerts every 2-5 minutes (demo-friendly)."""
    print("🚀 Alert generator thread started (Demo mode: 2-5 minute intervals)")
    while True:
        try:
            # Demo-friendly: Generate alerts every 2-5 minutes instead of 10-30 seconds
            delay = random.uniform(120, 300)  # 2-5 minutes
            print(f"⏰ Next alert in {delay/60:.1f} minutes...")
            time.sleep(delay)
            generate_alert()
        except Exception as e:
            print(f"❌ Error in alert generator thread: {e}")
            time.sleep(5)

# Start background thread on app startup
def start_background_threads():
    thread = threading.Thread(target=alert_generator_thread, daemon=True)
    thread.start()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'alert-service'}), 200

@app.route('/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts from database."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM alerts ORDER BY created_at DESC")
        alerts = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(alerts), 200
        
    except Exception as e:
        print(f"❌ Error: Failed to fetch alerts: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/alerts/manual', methods=['POST'])
def manual_alert():
    """Manually trigger an alert for demo purposes."""
    try:
        alert = generate_alert()
        if alert:
            return jsonify(alert), 201
        else:
            return jsonify({'error': 'Failed to generate alert'}), 500
    except Exception as e:
        print(f"❌ Error: Failed to create manual alert: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Start background thread
    start_background_threads()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8001, debug=False)
