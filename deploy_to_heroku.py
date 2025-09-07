"""
Automated Heroku Deployment Script for Word Counter Pro
This script automates the deployment process to Heroku
"""

import subprocess
import sys
import os
import time
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check if git is installed
    if not run_command("git --version", "Checking Git"):
        print("❌ Git is not installed. Please install Git first.")
        return False
    
    # Check if heroku CLI is installed
    if not run_command("heroku --version", "Checking Heroku CLI"):
        print("❌ Heroku CLI is not installed. Please install it first.")
        print("Download from: https://devcenter.heroku.com/articles/heroku-cli")
        return False
    
    # Check if user is logged in to Heroku
    if not run_command("heroku auth:whoami", "Checking Heroku login"):
        print("❌ Not logged in to Heroku. Please run 'heroku login' first.")
        return False
    
    print("✅ All prerequisites met!")
    return True

def create_heroku_app():
    """Create a new Heroku app"""
    app_name = input("Enter your Heroku app name (or press Enter for auto-generated): ").strip()
    
    if app_name:
        command = f"heroku create {app_name}"
    else:
        command = "heroku create"
    
    if not run_command(command, "Creating Heroku app"):
        return False
    
    # Get the app name from the output
    result = subprocess.run("heroku apps", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            app_name = lines[-1].split()[0]
            print(f"✅ Heroku app created: {app_name}")
            return app_name
    
    return False

def add_database():
    """Add PostgreSQL database to the app"""
    if not run_command("heroku addons:create heroku-postgresql:hobby-dev", "Adding PostgreSQL database"):
        return False
    
    print("✅ PostgreSQL database added!")
    return True

def prepare_files():
    """Prepare files for deployment"""
    print("📁 Preparing files for deployment...")
    
    # Check if Procfile exists
    if not Path("Procfile").exists():
        print("❌ Procfile not found. Creating one...")
        with open("Procfile", "w") as f:
            f.write("web: python backend_server_production.py")
    
    # Check if runtime.txt exists
    if not Path("runtime.txt").exists():
        print("❌ runtime.txt not found. Creating one...")
        with open("runtime.txt", "w") as f:
            f.write("python-3.11.0")
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found. Please create one first.")
        return False
    
    print("✅ Files prepared for deployment!")
    return True

def deploy_to_heroku():
    """Deploy the app to Heroku"""
    print("🚀 Deploying to Heroku...")
    
    # Initialize git if not already done
    if not Path(".git").exists():
        if not run_command("git init", "Initializing Git repository"):
            return False
    
    # Add all files
    if not run_command("git add .", "Adding files to Git"):
        return False
    
    # Commit files
    if not run_command('git commit -m "Deploy Word Counter Pro to Heroku"', "Committing files"):
        return False
    
    # Deploy to Heroku
    if not run_command("git push heroku main", "Deploying to Heroku"):
        return False
    
    print("✅ Deployment completed!")
    return True

def test_deployment():
    """Test the deployed app"""
    print("🧪 Testing deployment...")
    
    # Get the app URL
    result = subprocess.run("heroku apps:info", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.split('\n')
        app_url = None
        for line in lines:
            if 'Web URL:' in line:
                app_url = line.split('Web URL:')[1].strip()
                break
        
        if app_url:
            print(f"🌐 Your app is available at: {app_url}")
            
            # Test health endpoint
            import requests
            try:
                response = requests.get(f"{app_url}/health", timeout=10)
                if response.status_code == 200:
                    print("✅ Health check passed!")
                    print(f"📊 Response: {response.json()}")
                else:
                    print(f"❌ Health check failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Health check failed: {e}")
        else:
            print("❌ Could not determine app URL")
    else:
        print("❌ Could not get app information")

def update_cloud_sync_config():
    """Update cloud sync configuration with production URL"""
    print("🔧 Updating cloud sync configuration...")
    
    # Get the app URL
    result = subprocess.run("heroku apps:info", shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        lines = result.stdout.split('\n')
        app_url = None
        for line in lines:
            if 'Web URL:' in line:
                app_url = line.split('Web URL:')[1].strip()
                break
        
        if app_url:
            # Update cloud_sync.py
            cloud_sync_file = Path("cloud_sync.py")
            if cloud_sync_file.exists():
                content = cloud_sync_file.read_text()
                # Replace the API_BASE_URL
                content = content.replace(
                    'API_BASE_URL = "https://api.wordcounterpro.com"',
                    f'API_BASE_URL = "{app_url}"'
                )
                cloud_sync_file.write_text(content)
                print(f"✅ Updated cloud_sync.py with URL: {app_url}")
            else:
                print("❌ cloud_sync.py not found")
        else:
            print("❌ Could not determine app URL")

def main():
    """Main deployment function"""
    print("🚀 Word Counter Pro - Heroku Deployment Script")
    print("=" * 50)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install required tools and try again.")
        return
    
    print("\n" + "=" * 50)
    
    # Create Heroku app
    app_name = create_heroku_app()
    if not app_name:
        print("\n❌ Failed to create Heroku app. Please try again.")
        return
    
    print("\n" + "=" * 50)
    
    # Add database
    if not add_database():
        print("\n❌ Failed to add database. Please try again.")
        return
    
    print("\n" + "=" * 50)
    
    # Prepare files
    if not prepare_files():
        print("\n❌ Failed to prepare files. Please check the errors above.")
        return
    
    print("\n" + "=" * 50)
    
    # Deploy to Heroku
    if not deploy_to_heroku():
        print("\n❌ Deployment failed. Please check the errors above.")
        return
    
    print("\n" + "=" * 50)
    
    # Update configuration
    update_cloud_sync_config()
    
    print("\n" + "=" * 50)
    
    # Test deployment
    test_deployment()
    
    print("\n" + "=" * 50)
    print("🎉 Deployment completed successfully!")
    print("\nNext steps:")
    print("1. Test your app in the browser")
    print("2. Update your Word Counter Pro app to use the new URL")
    print("3. Start using cloud sync!")
    print("\nFor support, check the DEPLOYMENT_GUIDE.md file")

if __name__ == "__main__":
    main()

