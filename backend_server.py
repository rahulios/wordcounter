"""
Simple Backend Server for Word Counter Pro Cloud Sync
This is a basic Flask server for testing cloud sync functionality
In production, you would use a more robust solution like FastAPI or Django
"""

from flask import Flask, request, jsonify
from datetime import datetime
import json
import hashlib
import os
from typing import Dict, Any
import logging

app = Flask(__name__)

# In-memory storage for demo purposes
# In production, use a proper database like PostgreSQL or MongoDB
users_db = {}
sync_data_db = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

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
        
        # Check if user already exists
        if email in users_db or username in [user['username'] for user in users_db.values()]:
            return jsonify({"error": "Username or email already exists"}), 409
        
        # Create user
        user_id = hashlib.sha256(f"{email}{username}".encode()).hexdigest()[:16]
        user_data = {
            "user_id": user_id,
            "email": email,
            "username": username,
            "display_name": display_name,
            "password_hash": password_hash,
            "created_at": datetime.now().isoformat(),
            "subscription_tier": "free"
        }
        
        users_db[user_id] = user_data
        
        logger.info(f"User registered: {username} ({email})")
        
        return jsonify({
            "user_id": user_id,
            "email": email,
            "username": username,
            "display_name": display_name,
            "created_at": user_data["created_at"],
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
        
        # Find user by username or email
        user = None
        for user_data in users_db.values():
            if (user_data['username'] == username_or_email or 
                user_data['email'] == username_or_email):
                user = user_data
                break
        
        if not user:
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Verify password hash
        if user['password_hash'] != password_hash:
            return jsonify({"error": "Invalid username or password"}), 401
        
        logger.info(f"User logged in: {user['username']}")
        
        return jsonify({
            "user_id": user["user_id"],
            "email": user["email"],
            "username": user["username"],
            "display_name": user["display_name"],
            "created_at": user["created_at"],
            "subscription_tier": user["subscription_tier"]
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
        
        # Verify user exists
        if user_id not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        # Store sync data
        sync_data_db[user_id] = {
            "data": sync_data,
            "timestamp": timestamp,
            "uploaded_at": datetime.now().isoformat()
        }
        
        logger.info(f"Sync data uploaded for user: {user_id}")
        
        return jsonify({"status": "success", "message": "Data uploaded successfully"}), 200
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/sync/download/<user_id>', methods=['GET'])
def download_sync_data(user_id):
    """Download user sync data"""
    try:
        # Verify user exists
        if user_id not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        # Get sync data
        if user_id not in sync_data_db:
            return jsonify({"error": "No sync data found"}), 404
        
        sync_data = sync_data_db[user_id]
        
        logger.info(f"Sync data downloaded for user: {user_id}")
        
        return jsonify({
            "data": sync_data["data"],
            "timestamp": sync_data["timestamp"],
            "uploaded_at": sync_data["uploaded_at"]
        }), 200
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/user/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile"""
    try:
        if user_id not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        user_data = users_db[user_id]
        
        # Remove sensitive data
        profile_data = {
            "user_id": user_data["user_id"],
            "email": user_data["email"],
            "username": user_data["username"],
            "display_name": user_data["display_name"],
            "created_at": user_data["created_at"],
            "subscription_tier": user_data["subscription_tier"]
        }
        
        return jsonify(profile_data), 200
        
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
        
        if user_id not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        # Update subscription
        users_db[user_id]['subscription_tier'] = subscription_tier
        
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
    print("Starting Word Counter Pro Backend Server...")
    print("Server will be available at: http://localhost:5000")
    print("API Documentation:")
    print("  POST /auth/register - Register new user")
    print("  POST /auth/login - Login user")
    print("  POST /sync/upload - Upload sync data")
    print("  GET /sync/download/<user_id> - Download sync data")
    print("  GET /user/<user_id>/profile - Get user profile")
    print("  PUT /user/<user_id>/subscription - Update subscription")
    print("  GET /health - Health check")
    print("\nPress Ctrl+C to stop the server")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
