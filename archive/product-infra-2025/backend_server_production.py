"""
Production Backend Server for Word Counter Pro Cloud Sync
Optimized for Heroku deployment with PostgreSQL database
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import json
import hashlib
import os
import logging
from typing import Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import uuid

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    # Heroku PostgreSQL
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://')

def get_db_connection():
    """Get database connection"""
    try:
        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        else:
            # Local development
            conn = psycopg2.connect(
                host='localhost',
                database='wordcounter',
                user='postgres',
                password='password'
            )
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def init_database():
    """Initialize database tables"""
    conn = get_db_connection()
    if not conn:
        logger.error("Cannot connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                username VARCHAR(100) UNIQUE NOT NULL,
                display_name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                subscription_tier VARCHAR(20) DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        
        # Create sync_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_data (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(50) NOT NULL,
                data TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sync_data_user_id ON sync_data(user_id)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if get_db_connection() else "disconnected"
    })

@app.route('/auth/register', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'username', 'password_hash', 'display_name']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        email = data['email']
        username = data['username']
        password_hash = data['password_hash']
        display_name = data['display_name']
        
        # Generate unique user ID
        user_id = str(uuid.uuid4())[:16]
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT user_id FROM users WHERE email = %s OR username = %s", 
                      (email, username))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "Username or email already exists"}), 409
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (user_id, email, username, display_name, password_hash, subscription_tier)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, email, username, display_name, password_hash, 'free'))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"User registered: {username} ({email})")
        
        return jsonify({
            "user_id": user_id,
            "email": email,
            "username": username,
            "display_name": display_name,
            "created_at": datetime.now().isoformat(),
            "subscription_tier": "free"
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/auth/login', methods=['POST'])
def login_user():
    """Login existing user"""
    try:
        data = request.get_json()
        
        username_or_email = data.get('username_or_email')
        password_hash = data.get('password_hash')
        
        if not username_or_email or not password_hash:
            return jsonify({"error": "Username/email and password required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Find user by username or email
        cursor.execute("""
            SELECT user_id, email, username, display_name, password_hash, 
                   subscription_tier, created_at
            FROM users 
            WHERE username = %s OR email = %s
        """, (username_or_email, username_or_email))
        
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Verify password hash
        if user['password_hash'] != password_hash:
            cursor.close()
            conn.close()
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Update last login
        cursor.execute("UPDATE users SET last_login = %s WHERE user_id = %s", 
                      (datetime.now(), user['user_id']))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        logger.info(f"User logged in: {user['username']}")
        
        return jsonify({
            "user_id": user['user_id'],
            "email": user['email'],
            "username": user['username'],
            "display_name": user['display_name'],
            "created_at": user['created_at'].isoformat(),
            "subscription_tier": user['subscription_tier']
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/sync/upload', methods=['POST'])
def upload_sync_data():
    """Upload user sync data"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        sync_data = data.get('data')
        timestamp = data.get('timestamp')
        
        if not user_id or not sync_data:
            return jsonify({"error": "User ID and data required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Store sync data
        cursor.execute("""
            INSERT INTO sync_data (user_id, data, timestamp, uploaded_at)
            VALUES (%s, %s, %s, %s)
        """, (user_id, sync_data, timestamp, datetime.now()))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Sync data uploaded for user: {user_id}")
        
        return jsonify({"status": "success", "message": "Data uploaded successfully"}), 200
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/sync/download/<user_id>', methods=['GET'])
def download_sync_data(user_id):
    """Download user sync data"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Verify user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Get latest sync data
        cursor.execute("""
            SELECT data, timestamp, uploaded_at
            FROM sync_data 
            WHERE user_id = %s 
            ORDER BY uploaded_at DESC 
            LIMIT 1
        """, (user_id,))
        
        sync_record = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not sync_record:
            return jsonify({"error": "No sync data found"}), 404
        
        logger.info(f"Sync data downloaded for user: {user_id}")
        
        return jsonify({
            "data": sync_record['data'],
            "timestamp": sync_record['timestamp'].isoformat(),
            "uploaded_at": sync_record['uploaded_at'].isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/user/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT user_id, email, username, display_name, subscription_tier, created_at, last_login
            FROM users 
            WHERE user_id = %s
        """, (user_id,))
        
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "user_id": user['user_id'],
            "email": user['email'],
            "username": user['username'],
            "display_name": user['display_name'],
            "subscription_tier": user['subscription_tier'],
            "created_at": user['created_at'].isoformat(),
            "last_login": user['last_login'].isoformat() if user['last_login'] else None
        }), 200
        
    except Exception as e:
        logger.error(f"Profile error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/user/<user_id>/subscription', methods=['PUT'])
def update_subscription(user_id):
    """Update user subscription tier"""
    try:
        data = request.get_json()
        subscription_tier = data.get('subscription_tier')
        
        if not subscription_tier:
            return jsonify({"error": "Subscription tier required"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "Database connection failed"}), 500
        
        cursor = conn.cursor()
        
        # Verify user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "User not found"}), 404
        
        # Update subscription
        cursor.execute("UPDATE users SET subscription_tier = %s WHERE user_id = %s", 
                      (subscription_tier, user_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Subscription updated for user {user_id}: {subscription_tier}")
        
        return jsonify({"status": "success", "subscription_tier": subscription_tier}), 200
        
    except Exception as e:
        logger.error(f"Subscription update error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Initialize database
    if init_database():
        print("✅ Database initialized successfully")
    else:
        print("❌ Database initialization failed")
    
    # Get port from environment (Heroku sets this)
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Starting Word Counter Pro Backend Server...")
    print(f"🌐 Server will be available at: http://localhost:{port}")
    print(f"📊 Database: {'Connected' if get_db_connection() else 'Disconnected'}")
    print(f"🔧 Environment: {'Production' if DATABASE_URL else 'Development'}")
    
    app.run(host='0.0.0.0', port=port, debug=False)

