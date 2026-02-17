from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
import pika
import os
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
import json
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO for real-time notifications
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Prometheus Metrics
notifications_sent_total = Counter('notifications_sent_total', 'Total notifications sent', ['type', 'channel'])
notifications_delivered_total = Counter('notifications_delivered_total', 'Total notifications delivered', ['channel'])

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hospital')
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')

# Track connected employees (employee_id -> socket_id)
connected_employees = {}

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

def save_notification_to_db(notification_data):
    """Save notification to database for history."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO notifications (
                employee_id, 
                incident_id, 
                type, 
                title,
                message, 
                severity,
                data,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            notification_data.get('employee_id'),
            notification_data.get('incident_id'),
            notification_data.get('type'),
            notification_data.get('title'),
            notification_data.get('message'),
            notification_data.get('severity'),
            json.dumps(notification_data.get('data', {})),
            datetime.now()
        ))
        
        conn.commit()
        cur.close()
        return_db_connection(conn)
        
        print(f"✅ Notification saved to database for employee {notification_data.get('employee_id')}")
        return True
        
    except Exception as e:
        print(f"❌ Error saving notification: {e}")
        return False

def send_websocket_notification(employee_id, notification_data):
    """Send real-time WebSocket notification to employee."""
    try:
        if employee_id in connected_employees:
            socketio.emit('new_notification', notification_data, room=f"employee_{employee_id}")
            print(f"✅ WebSocket notification sent to employee {employee_id}")
            return True
        else:
            print(f"⚠️  Employee {employee_id} not connected via WebSocket")
            return False
    except Exception as e:
        print(f"❌ Error sending WebSocket notification: {e}")
        return False

def process_notification(notification_data):
    """Process notification - save to database and send via WebSocket."""
    try:
        notification_type = notification_data.get('type')
        severity = notification_data.get('severity', 'MEDIUM')
        employee_id = notification_data.get('employee_id')
        
        print(f"\n{'='*60}")
        print(f"🔔 Processing Notification:")
        print(f"   Type: {notification_type}")
        print(f"   Severity: {severity}")
        print(f"   Employee: {notification_data.get('employee_name')} (ID: {employee_id})")
        print(f"   Incident: {notification_data.get('incident_id')}")
        print(f"{'='*60}\n")
        
        # 1. Save to database for persistence
        save_notification_to_db(notification_data)
        
        # 2. Send real-time WebSocket notification
        send_websocket_notification(employee_id, notification_data)
        
        print(f"✅ Notification processed successfully\n")
        return True
        
    except Exception as e:
        print(f"❌ Error processing notification: {e}")
        return False

def process_notification_message(ch, method, properties, body):
    """Callback function to process notifications from RabbitMQ."""
    try:
        notification_data = json.loads(body)
        process_notification(notification_data)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"❌ Error: Failed to process notification message: {e}")
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
    """Background thread that listens to RabbitMQ notifications queue."""
    print("🚀 Notification Service: RabbitMQ consumer thread started")
    while True:
        try:
            connection = get_rabbitmq_connection()
            if not connection:
                print("❌ Error: Could not establish RabbitMQ connection, retrying in 10s...")
                time.sleep(10)
                continue
                
            channel = connection.channel()
            channel.queue_declare(queue='notifications', durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='notifications', on_message_callback=process_notification_message)
            
            print("✅ Listening for notifications on RabbitMQ queue 'notifications'")
            channel.start_consuming()
            
        except Exception as e:
            print(f"❌ Error: RabbitMQ consumer error: {e}")
            time.sleep(10)

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    print(f"🔌 Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"🔌 Client disconnected: {request.sid}")
    # Remove from connected employees
    for emp_id, sid in list(connected_employees.items()):
        if sid == request.sid:
            del connected_employees[emp_id]
            print(f"👤 Employee {emp_id} disconnected")
            break

@socketio.on('register_employee')
def handle_register_employee(data):
    """Register employee for receiving notifications."""
    employee_id = data.get('employee_id')
    if employee_id:
        connected_employees[employee_id] = request.sid
        join_room(f"employee_{employee_id}")
        print(f"✅ Employee {employee_id} registered for notifications")
        emit('registration_success', {'employee_id': employee_id})

@socketio.on('mark_notification_read')
def handle_mark_read(data):
    """Mark notification as read."""
    notification_id = data.get('notification_id')
    try:
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("""
                UPDATE notifications 
                SET is_read = TRUE, read_at = %s
                WHERE notification_id = %s
            """, (datetime.now(), notification_id))
            conn.commit()
            cur.close()
            return_db_connection(conn)
            emit('notification_marked_read', {'notification_id': notification_id})
    except Exception as e:
        print(f"❌ Error marking notification as read: {e}")

# REST API endpoints
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'notification-service',
        'connected_employees': len(connected_employees)
    }), 200

@app.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/notifications/<int:employee_id>', methods=['GET'])
def get_employee_notifications(employee_id):
    """Get all notifications for an employee."""
    try:
        unread_only = request.args.get('unread', 'false').lower() == 'true'
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        if unread_only:
            cur.execute("""
                SELECT * FROM notifications 
                WHERE employee_id = %s AND is_read = FALSE
                ORDER BY created_at DESC
            """, (employee_id,))
        else:
            cur.execute("""
                SELECT * FROM notifications 
                WHERE employee_id = %s
                ORDER BY created_at DESC
                LIMIT 50
            """, (employee_id,))
        
        notifications = cur.fetchall()
        cur.close()
        return_db_connection(conn)
        
        return jsonify(notifications), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/notifications/<int:notification_id>/read', methods=['PATCH'])
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor()
        cur.execute("""
            UPDATE notifications 
            SET is_read = TRUE, read_at = %s
            WHERE notification_id = %s
        """, (datetime.now(), notification_id))
        
        conn.commit()
        cur.close()
        return_db_connection(conn)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/notifications/employee/<int:employee_id>/mark-all-read', methods=['PATCH'])
def mark_all_read(employee_id):
    """Mark all notifications as read for an employee."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor()
        cur.execute("""
            UPDATE notifications 
            SET is_read = TRUE, read_at = %s
            WHERE employee_id = %s AND is_read = FALSE
        """, (datetime.now(), employee_id))
        
        updated_count = cur.rowcount
        conn.commit()
        cur.close()
        return_db_connection(conn)
        
        return jsonify({'success': True, 'updated_count': updated_count}), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/notifications/incident/<incident_id>/mark-read', methods=['PATCH'])
def mark_incident_notification_read(incident_id):
    """Mark all notifications for a specific incident as read."""
    try:
        data = request.get_json()
        employee_id = data.get('employee_id')
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cur = conn.cursor()
        cur.execute("""
            UPDATE notifications 
            SET is_read = TRUE, read_at = %s
            WHERE incident_id = %s AND employee_id = %s AND is_read = FALSE
        """, (datetime.now(), incident_id, employee_id))
        
        conn.commit()
        updated_count = cur.rowcount
        cur.close()
        return_db_connection(conn)
        
        print(f"✅ Marked {updated_count} notifications as read for incident {incident_id}")
        
        return jsonify({
            'message': f'Marked {updated_count} notifications as read',
            'incident_id': incident_id,
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'error': str(e)}), 500

# Start background thread
consumer_thread = threading.Thread(target=rabbitmq_consumer_thread, daemon=True)
consumer_thread.start()

if __name__ == '__main__':
    # Run with SocketIO
    socketio.run(app, host='0.0.0.0', port=8004, debug=False, allow_unsafe_werkzeug=True)
