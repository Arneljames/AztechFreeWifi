import os
import sqlite3
import subprocess
import re
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, render_template

app = Flask(__name__, static_folder='static')
DB_PATH = 'wifi_users.db'

# Helper function to get client MAC from IP
def get_mac_address(ip):
    # Try to find MAC from arp table or ip neighbor
    try:
        # Command to get neighbor info for specific IP
        output = subprocess.check_output(['ip', 'neigh', 'show', ip], text=True)
        # Regex for MAC address
        mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})', output)
        if mac_match:
            return mac_match.group(0).lower()
        
        # Fallback to arp command
        output = subprocess.check_output(['arp', '-n', ip], text=True)
        mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}([0-9a-fA-F]{2})', output)
        if mac_match:
            return mac_match.group(0).lower()
    except Exception as e:
        print(f"Error getting MAC address: {e}")
    
    return None

def db_query(query, args=(), one=False):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/unlock', methods=['POST'])
def unlock():
    client_ip = request.remote_addr
    # For testing, allow override via param if not on real network
    client_mac = request.args.get('mac') or get_mac_address(client_ip)
    
    if not client_mac:
        return jsonify({"success": False, "message": "Could not identify your device MAC."}), 400
    
    today = date.today().isoformat()
    
    # Check if MAC already used today
    existing = db_query("SELECT id FROM users WHERE mac_address = ? AND date_used = ?", (client_mac, today), one=True)
    if existing:
        return jsonify({"success": False, "message": "You have already used your free hour for today. Please try again tomorrow."}), 403
    
    # Grant access
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=1)
    
    try:
        # Insert into DB
        db_query("INSERT INTO users (mac_address, ip_address, date_used, session_start, session_end) VALUES (?, ?, ?, ?, ?)",
                 (client_mac, client_ip, today, start_time.isoformat(), end_time.isoformat()))
        
        # Add iptables rule
        # Note: This requires the Flask app to run as root or have sudo privileges
        subprocess.run(['sudo', 'iptables', '-I', 'FORWARD', '-s', client_ip, '-j', 'ACCEPT'], check=True)
        
        return jsonify({
            "success": True, 
            "message": "Access granted! You have 60 minutes.",
            "duration": 3600,
            "mac": client_mac
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"System error: {str(e)}"}), 500

@app.route('/expire', methods=['POST'])
def expire():
    client_ip = request.remote_addr
    try:
        # Remove iptables rule
        subprocess.run(['sudo', 'iptables', '-D', 'FORWARD', '-s', client_ip, '-j', 'ACCEPT'], check=False)
        return jsonify({"success": True, "message": "Session expired."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/admin')
def admin():
    users = db_query("SELECT * FROM users ORDER BY session_start DESC")
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    # Ensure DB exists
    if not os.path.exists(DB_PATH):
        print("Database not found. Please run schema setup.")
    
    # Armbian/Linux default port 80 or 8080
    app.run(host='0.0.0.0', port=8080)
