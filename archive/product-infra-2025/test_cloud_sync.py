"""
Test script for Word Counter Pro Cloud Sync functionality
This script tests the cloud sync features without requiring the full GUI
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_cloud_sync_imports():
    """Test that all cloud sync modules can be imported"""
    print("Testing cloud sync imports...")
    
    try:
        from cloud_sync import cloud_sync_manager, UserProfile, SyncData
        print("✓ cloud_sync module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import cloud_sync: {e}")
        return False
    
    try:
        from auth_ui import LoginDialog, RegisterDialog, AccountManagerDialog
        print("✓ auth_ui module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import auth_ui: {e}")
        return False
    
    try:
        from cloud_integration import CloudIntegration
        print("✓ cloud_integration module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import cloud_integration: {e}")
        return False
    
    return True

def test_encryption():
    """Test encryption functionality"""
    print("\nTesting encryption...")
    
    try:
        from cloud_sync import EncryptionManager
        
        # Test encryption manager
        enc_manager = EncryptionManager()
        test_password = "test_password_123"
        
        # Test key generation
        if enc_manager.load_or_create_key(test_password):
            print("✓ Encryption key created/loaded successfully")
            
            # Test encryption/decryption
            test_data = "This is test data for encryption"
            encrypted = enc_manager.encrypt_data(test_data)
            decrypted = enc_manager.decrypt_data(encrypted)
            
            if decrypted == test_data:
                print("✓ Encryption/decryption working correctly")
                return True
            else:
                print("✗ Encryption/decryption failed - data mismatch")
                return False
        else:
            print("✗ Failed to create/load encryption key")
            return False
            
    except Exception as e:
        print(f"✗ Encryption test failed: {e}")
        return False

def test_user_profile():
    """Test user profile functionality"""
    print("\nTesting user profile...")
    
    try:
        from cloud_sync import UserProfile
        
        # Create test user profile
        profile = UserProfile(
            user_id="test_user_123",
            email="test@example.com",
            username="testuser",
            display_name="Test User",
            created_at=datetime.now(),
            subscription_tier="free"
        )
        
        print(f"✓ User profile created: {profile.username}")
        print(f"  - Email: {profile.email}")
        print(f"  - Subscription: {profile.subscription_tier}")
        
        return True
        
    except Exception as e:
        print(f"✗ User profile test failed: {e}")
        return False

def test_sync_data():
    """Test sync data structure"""
    print("\nTesting sync data structure...")
    
    try:
        from cloud_sync import SyncData
        
        # Create test sync data
        sync_data = SyncData(
            user_id="test_user_123",
            sessions=[
                {
                    "date_time": datetime.now().isoformat(),
                    "word_count": 100,
                    "duration": 300,
                    "wpm": 20.0,
                    "productivity_score": 85.5
                }
            ],
            goals=[],
            achievements=[],
            settings={"theme": "clam", "daily_goal": 1000},
            last_modified=datetime.now(),
            version=1
        )
        
        print(f"✓ Sync data created with {len(sync_data.sessions)} sessions")
        print(f"  - User ID: {sync_data.user_id}")
        print(f"  - Version: {sync_data.version}")
        
        return True
        
    except Exception as e:
        print(f"✗ Sync data test failed: {e}")
        return False

def test_cloud_sync_manager():
    """Test cloud sync manager functionality"""
    print("\nTesting cloud sync manager...")
    
    try:
        from cloud_sync import cloud_sync_manager
        
        # Test connectivity check
        print("Checking connectivity...")
        is_online = cloud_sync_manager.check_connectivity()
        print(f"  - Online status: {is_online}")
        
        # Test sync status
        sync_status = cloud_sync_manager.get_sync_status()
        print(f"  - User logged in: {sync_status['user_logged_in']}")
        print(f"  - Is online: {sync_status['is_online']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Cloud sync manager test failed: {e}")
        return False

def test_backend_server():
    """Test backend server functionality"""
    print("\nTesting backend server...")
    
    try:
        import requests
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:5000/health", timeout=5)
            if response.status_code == 200:
                print("✓ Backend server is running")
                return True
            else:
                print(f"✗ Backend server returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("✗ Backend server is not running")
            print("  Start it with: python backend_server.py")
            return False
            
    except ImportError:
        print("✗ Requests module not available")
        return False
    except Exception as e:
        print(f"✗ Backend server test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Word Counter Pro - Cloud Sync Test Suite")
    print("=" * 50)
    
    tests = [
        test_cloud_sync_imports,
        test_encryption,
        test_user_profile,
        test_sync_data,
        test_cloud_sync_manager,
        test_backend_server
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Cloud sync is ready to use.")
        print("\nNext steps:")
        print("1. Start the backend server: python backend_server.py")
        print("2. Run the setup wizard: python setup_cloud_sync.py")
        print("3. Launch the enhanced app: python wordcounter_with_cloud.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Check Python version (3.8+ required)")
        print("3. Verify all files are in the same directory")

if __name__ == "__main__":
    main()
