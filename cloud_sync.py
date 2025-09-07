"""
Cloud Sync and User Authentication Module for Word Counter Pro
Handles user accounts, data synchronization, and cloud storage
"""

import json
import hashlib
import hmac
import base64
import requests
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

# Configuration
API_BASE_URL = "https://api.wordcounterpro.com"  # Replace with your actual API
ENCRYPTION_KEY_FILE = "user_key.key"
USER_DATA_FILE = "user_data.json"

@dataclass
class UserProfile:
    """User profile information"""
    user_id: str
    email: str
    username: str
    display_name: str
    created_at: datetime
    last_sync: Optional[datetime] = None
    subscription_tier: str = "free"  # free, pro, team
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}

@dataclass
class SyncData:
    """Data structure for cloud synchronization"""
    user_id: str
    sessions: List[Dict[str, Any]]
    goals: List[Dict[str, Any]]
    achievements: List[Dict[str, Any]]
    settings: Dict[str, Any]
    last_modified: datetime
    version: int = 1

class EncryptionManager:
    """Handles data encryption for cloud storage"""
    
    def __init__(self, password: str = None):
        self.password = password
        self.key = None
        self.cipher = None
        
    def generate_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """Generate encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    def load_or_create_key(self, password: str) -> bool:
        """Load existing key or create new one"""
        try:
            key_file = Path(ENCRYPTION_KEY_FILE)
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key_data = f.read()
                    salt = key_data[:16]
                    stored_key = key_data[16:]
                    
                    # Verify password by attempting to decrypt
                    key, _ = self.generate_key_from_password(password, salt)
                    if key == stored_key:
                        self.key = key
                        self.cipher = Fernet(key)
                        return True
                    else:
                        return False
            else:
                # Create new key
                key, salt = self.generate_key_from_password(password)
                self.key = key
                self.cipher = Fernet(key)
                
                # Save key file
                with open(key_file, 'wb') as f:
                    f.write(salt + key)
                return True
                
        except Exception as e:
            logging.error(f"Error loading/creating encryption key: {e}")
            return False
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt data for cloud storage"""
        if not self.cipher:
            raise ValueError("Encryption not initialized")
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data from cloud storage"""
        if not self.cipher:
            raise ValueError("Encryption not initialized")
        return self.cipher.decrypt(encrypted_data.encode()).decode()

class CloudSyncManager:
    """Manages cloud synchronization and user authentication"""
    
    def __init__(self):
        self.user_profile: Optional[UserProfile] = None
        self.encryption_manager = EncryptionManager()
        self.is_online = False
        self.sync_in_progress = False
        self.last_sync_time = None
        self.sync_interval = 300  # 5 minutes
        self.api_base = API_BASE_URL
        
        # Start background sync thread
        self.sync_thread = threading.Thread(target=self._background_sync, daemon=True)
        self.sync_thread.start()
    
    def register_user(self, email: str, username: str, password: str, display_name: str = None) -> Tuple[bool, str]:
        """Register a new user account"""
        try:
            # Validate input
            if not email or not username or not password:
                return False, "All fields are required"
            
            if len(password) < 8:
                return False, "Password must be at least 8 characters"
            
            # Hash password for transmission
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Prepare registration data
            registration_data = {
                "email": email,
                "username": username,
                "password_hash": password_hash,
                "display_name": display_name or username,
                "created_at": datetime.now().isoformat()
            }
            
            # Send registration request
            response = requests.post(
                f"{self.api_base}/auth/register",
                json=registration_data,
                timeout=10
            )
            
            if response.status_code == 201:
                # Registration successful
                user_data = response.json()
                self.user_profile = UserProfile(
                    user_id=user_data["user_id"],
                    email=email,
                    username=username,
                    display_name=display_name or username,
                    created_at=datetime.fromisoformat(user_data["created_at"])
                )
                
                # Initialize encryption
                if self.encryption_manager.load_or_create_key(password):
                    self._save_user_data()
                    self.is_online = True
                    return True, "Registration successful"
                else:
                    return False, "Failed to initialize encryption"
            
            elif response.status_code == 409:
                return False, "Username or email already exists"
            else:
                return False, f"Registration failed: {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logging.error(f"Registration error: {e}")
            return False, f"Registration failed: {str(e)}"
    
    def login_user(self, username_or_email: str, password: str) -> Tuple[bool, str]:
        """Login existing user"""
        try:
            # Hash password for transmission
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Prepare login data
            login_data = {
                "username_or_email": username_or_email,
                "password_hash": password_hash
            }
            
            # Send login request
            response = requests.post(
                f"{self.api_base}/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                # Login successful
                user_data = response.json()
                self.user_profile = UserProfile(
                    user_id=user_data["user_id"],
                    email=user_data["email"],
                    username=user_data["username"],
                    display_name=user_data["display_name"],
                    created_at=datetime.fromisoformat(user_data["created_at"]),
                    subscription_tier=user_data.get("subscription_tier", "free")
                )
                
                # Initialize encryption
                if self.encryption_manager.load_or_create_key(password):
                    self._save_user_data()
                    self.is_online = True
                    return True, "Login successful"
                else:
                    return False, "Failed to initialize encryption"
            
            elif response.status_code == 401:
                return False, "Invalid username or password"
            else:
                return False, f"Login failed: {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logging.error(f"Login error: {e}")
            return False, f"Login failed: {str(e)}"
    
    def logout_user(self) -> None:
        """Logout current user"""
        self.user_profile = None
        self.encryption_manager = EncryptionManager()
        self.is_online = False
        
        # Remove local user data
        user_data_file = Path(USER_DATA_FILE)
        if user_data_file.exists():
            user_data_file.unlink()
    
    def sync_data_to_cloud(self, local_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Sync local data to cloud"""
        if not self.user_profile or not self.is_online:
            return False, "User not logged in or offline"
        
        try:
            # Prepare sync data
            sync_data = SyncData(
                user_id=self.user_profile.user_id,
                sessions=local_data.get("sessions", []),
                goals=local_data.get("goals", []),
                achievements=local_data.get("achievements", []),
                settings=local_data.get("settings", {}),
                last_modified=datetime.now(),
                version=local_data.get("version", 1)
            )
            
            # Encrypt data
            encrypted_data = self.encryption_manager.encrypt_data(json.dumps(asdict(sync_data), default=str))
            
            # Send to cloud
            response = requests.post(
                f"{self.api_base}/sync/upload",
                json={
                    "user_id": self.user_profile.user_id,
                    "data": encrypted_data,
                    "timestamp": datetime.now().isoformat()
                },
                timeout=30
            )
            
            if response.status_code == 200:
                self.last_sync_time = datetime.now()
                self.user_profile.last_sync = self.last_sync_time
                self._save_user_data()
                return True, "Data synced successfully"
            else:
                return False, f"Sync failed: {response.text}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}"
        except Exception as e:
            logging.error(f"Sync error: {e}")
            return False, f"Sync failed: {str(e)}"
    
    def sync_data_from_cloud(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Sync data from cloud to local"""
        if not self.user_profile or not self.is_online:
            return False, "User not logged in or offline", None
        
        try:
            # Get data from cloud
            response = requests.get(
                f"{self.api_base}/sync/download/{self.user_profile.user_id}",
                timeout=30
            )
            
            if response.status_code == 200:
                cloud_data = response.json()
                encrypted_data = cloud_data["data"]
                
                # Decrypt data
                decrypted_data = self.encryption_manager.decrypt_data(encrypted_data)
                sync_data = json.loads(decrypted_data)
                
                # Convert back to proper format
                local_data = {
                    "sessions": sync_data["sessions"],
                    "goals": sync_data["goals"],
                    "achievements": sync_data["achievements"],
                    "settings": sync_data["settings"],
                    "version": sync_data["version"],
                    "last_modified": sync_data["last_modified"]
                }
                
                self.last_sync_time = datetime.now()
                self.user_profile.last_sync = self.last_sync_time
                self._save_user_data()
                
                return True, "Data synced successfully", local_data
            
            elif response.status_code == 404:
                return True, "No cloud data found", {}
            else:
                return False, f"Sync failed: {response.text}", None
                
        except requests.exceptions.RequestException as e:
            return False, f"Network error: {str(e)}", None
        except Exception as e:
            logging.error(f"Sync error: {e}")
            return False, f"Sync failed: {str(e)}", None
    
    def _background_sync(self) -> None:
        """Background thread for automatic syncing"""
        while True:
            try:
                if (self.user_profile and self.is_online and 
                    not self.sync_in_progress and
                    (not self.last_sync_time or 
                     datetime.now() - self.last_sync_time > timedelta(seconds=self.sync_interval))):
                    
                    self.sync_in_progress = True
                    # This would be called from the main app with actual data
                    # self.sync_data_to_cloud(local_data)
                    self.sync_in_progress = False
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logging.error(f"Background sync error: {e}")
                self.sync_in_progress = False
                time.sleep(60)
    
    def _save_user_data(self) -> None:
        """Save user data to local file"""
        try:
            user_data = {
                "user_profile": asdict(self.user_profile) if self.user_profile else None,
                "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
                "is_online": self.is_online
            }
            
            with open(USER_DATA_FILE, 'w') as f:
                json.dump(user_data, f, default=str, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving user data: {e}")
    
    def load_user_data(self) -> bool:
        """Load user data from local file"""
        try:
            user_data_file = Path(USER_DATA_FILE)
            if not user_data_file.exists():
                return False
            
            with open(user_data_file, 'r') as f:
                user_data = json.load(f)
            
            if user_data.get("user_profile"):
                profile_data = user_data["user_profile"]
                self.user_profile = UserProfile(
                    user_id=profile_data["user_id"],
                    email=profile_data["email"],
                    username=profile_data["username"],
                    display_name=profile_data["display_name"],
                    created_at=datetime.fromisoformat(profile_data["created_at"]),
                    last_sync=datetime.fromisoformat(profile_data["last_sync"]) if profile_data.get("last_sync") else None,
                    subscription_tier=profile_data.get("subscription_tier", "free"),
                    preferences=profile_data.get("preferences", {})
                )
            
            self.is_online = user_data.get("is_online", False)
            self.last_sync_time = datetime.fromisoformat(user_data["last_sync"]) if user_data.get("last_sync") else None
            
            return True
            
        except Exception as e:
            logging.error(f"Error loading user data: {e}")
            return False
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        return {
            "is_online": self.is_online,
            "user_logged_in": self.user_profile is not None,
            "last_sync": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "sync_in_progress": self.sync_in_progress,
            "subscription_tier": self.user_profile.subscription_tier if self.user_profile else "free"
        }
    
    def check_connectivity(self) -> bool:
        """Check if internet connection is available"""
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            self.is_online = response.status_code == 200
            return self.is_online
        except:
            self.is_online = False
            return False

# Global instance
cloud_sync_manager = CloudSyncManager()
