from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/hospital')
print(f"🔍 Using DATABASE_URL: {DATABASE_URL}")

def get_db_connection():
    """Get database connection with retry logic."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Error: Database connection failed: {e}")
        return None

def seed_oncall_schedules():
    """Seed initial on-call schedule data on startup by linking employees to shifts."""
    try:
        conn = get_db_connection()
        if not conn:
            return False
            
        cur = conn.cursor()
        
        # Check if schedules already exist
        cur.execute("SELECT COUNT(*) FROM oncall_schedules")
        count = cur.fetchone()[0]
        
        if count > 0:
            print("✅ On-call schedules already seeded")
            cur.close()
            conn.close()
            return True
        
        # Get current date at midnight
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get all employees from database with their shift times
        cur.execute("""
            SELECT employee_id, login, name, role, tier, shift_start_time, shift_end_time 
            FROM employees 
            ORDER BY role, tier
        """)
        employees = cur.fetchall()
        
        if not employees:
            print("⚠️  Warning: No employees found in database. Run employees.sql first!")
            cur.close()
            conn.close()
            return False
        
        # Create schedules for all employees using their defined shift times
        for emp in employees:
            employee_id, login, name, role, tier, shift_start_time, shift_end_time = emp
            
            # Combine today's date with employee's shift times
            shift_start = datetime.combine(today, shift_start_time)
            shift_end = datetime.combine(today, shift_end_time)
            
            # If shift ends at midnight or after, it means next day
            if shift_end_time < shift_start_time:
                shift_end = shift_end + timedelta(days=1)
            
            cur.execute("""
                INSERT INTO oncall_schedules (employee_id, role, person_name, tier, shift_start, shift_end)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (employee_id, role, name, tier, shift_start, shift_end))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"✅ Seeded {len(employees)} on-call schedules from employees table")
        return True
        
    except Exception as e:
        print(f"❌ Error: Failed to seed schedules: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'oncall-service'}), 200

@app.route('/auth/login', methods=['POST'])
def employee_login():
    """Employee login endpoint."""
    try:
        data = request.get_json()
        
        if not data or 'login' not in data or 'password' not in data:
            return jsonify({'error': 'login and password are required'}), 400
        
        login = data['login']
        password = data['password']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verify credentials
        cur.execute("""
            SELECT employee_id, login, name, email, role, tier
            FROM employees 
            WHERE login = %s AND password = %s
        """, (login, password))
        
        employee = cur.fetchone()
        
        if not employee:
            cur.close()
            conn.close()
            return jsonify({'error': 'Invalid login or password'}), 401
        
        # Update login status
        cur.execute("""
            UPDATE employees 
            SET is_logged_in = TRUE, last_login = %s
            WHERE login = %s
        """, (datetime.now(), login))
        conn.commit()
        
        cur.close()
        conn.close()
        
        print(f"✅ Employee logged in: {employee['name']} ({login})")
        return jsonify({
            'message': 'Login successful',
            'employee': employee
        }), 200
        
    except Exception as e:
        print(f"❌ Error: Login failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/auth/logout', methods=['POST'])
def employee_logout():
    """Employee logout endpoint."""
    try:
        data = request.get_json()
        
        if not data or 'login' not in data:
            return jsonify({'error': 'login is required'}), 400
        
        login = data['login']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Update logout status
        cur.execute("""
            UPDATE employees 
            SET is_logged_in = FALSE
            WHERE login = %s
        """, (login,))
        conn.commit()
        
        cur.close()
        conn.close()
        
        print(f"✅ Employee logged out: {login}")
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        print(f"❌ Error: Logout failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/oncall/current', methods=['GET'])
def get_current_oncall():
    """Get who's currently logged in and on-call for a specific role."""
    try:
        role = request.args.get('role')
        
        if not role:
            return jsonify({'error': 'role parameter is required'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Find employees who are logged in for the specified role
        cur.execute("""
            SELECT employee_id, login, name, role, tier, last_login
            FROM employees 
            WHERE role = %s AND is_logged_in = TRUE
            ORDER BY tier ASC
        """, (role,))
        
        employees = cur.fetchall()
        cur.close()
        conn.close()
        
        if not employees:
            return jsonify({'error': f'No one currently logged in for role {role}'}), 404
            
        return jsonify(employees), 200
        
    except Exception as e:
        print(f"❌ Error: Failed to fetch logged-in employees: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/oncall/assign', methods=['POST'])
def assign_oncall():
    """Assign an incident to a specific employee."""
    try:
        data = request.get_json()
        
        if not data or 'incident_id' not in data or 'employee_id' not in data:
            return jsonify({'error': 'incident_id and employee_id are required'}), 400
        
        incident_id = data['incident_id']
        employee_id = data['employee_id']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get employee details
        cur.execute("""
            SELECT employee_id, login, name, email, phone, role, tier
            FROM employees 
            WHERE employee_id = %s
        """, (employee_id,))
        
        employee = cur.fetchone()
        
        if not employee:
            cur.close()
            conn.close()
            return jsonify({'error': f'Employee with ID {employee_id} not found'}), 404
        
        person_name = employee['name']
        
        # Update incident with assignment
        cur.execute("""
            UPDATE incidents 
            SET assigned_to = %s, 
                assigned_employee_id = %s,
                assigned_at = %s,
                status = 'ASSIGNED'
            WHERE incident_id = %s
        """, (person_name, employee_id, datetime.now(), incident_id))
        conn.commit()
        
        # Fetch updated incident
        cur.execute("SELECT * FROM incidents WHERE incident_id = %s", (incident_id,))
        incident = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not incident:
            return jsonify({'error': 'Incident not found'}), 404
        
        print(f"✅ Assigned incident {incident_id} to {person_name} (ID: {employee_id})")
        return jsonify({
            'incident': incident,
            'assigned_to': person_name,
            'employee': employee
        }), 200
        
    except Exception as e:
        print(f"❌ Error: Failed to assign incident: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/oncall/schedules', methods=['GET'])
def get_schedules():
    """Get all employees and their login status."""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'error': 'Database connection failed'}), 500
            
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT employee_id, login, name, role, tier, is_logged_in, last_login
            FROM employees 
            ORDER BY role, tier
        """)
        employees = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(employees), 200
        
    except Exception as e:
        print(f"❌ Error: Failed to fetch employees: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Seed schedules on startup
    seed_oncall_schedules()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=8003, debug=False)
