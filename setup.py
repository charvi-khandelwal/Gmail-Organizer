#!/usr/bin/env python3
"""
Setup script for Email Organizer
Creates necessary configuration files and guides users through setup
"""

import os
import json
import sys
from pathlib import Path

def create_gmail_credentials():
    """Create Gmail credentials template"""
    gmail_creds = {
        "installed": {
            "client_id": "YOUR_GMAIL_CLIENT_ID_HERE",
            "client_secret": "YOUR_GMAIL_CLIENT_SECRET_HERE",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open('gmail_credentials.json', 'w') as f:
        json.dump(gmail_creds, f, indent=2)
    
    print("✅ Created gmail_credentials.json")
    print("📝 Please update with your Gmail API credentials")

def create_outlook_credentials():
    """Create Outlook credentials template"""
    outlook_creds = {
        "client_id": "YOUR_OUTLOOK_CLIENT_ID_HERE",
        "client_secret": "YOUR_OUTLOOK_CLIENT_SECRET_HERE",
        "tenant_id": "YOUR_TENANT_ID_HERE (optional, use 'common' for personal accounts)"
    }
    
    with open('outlook_credentials.json', 'w') as f:
        json.dump(outlook_creds, f, indent=2)
    
    print("✅ Created outlook_credentials.json")
    print("📝 Please update with your Outlook API credentials")

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    
    try:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✅ Python version compatible: {version.major}.{version.minor}.{version.micro}")
        return True

def print_setup_instructions():
    """Print detailed setup instructions"""
    print("\n" + "="*60)
    print("🚀 EMAIL ORGANIZER SETUP INSTRUCTIONS")
    print("="*60)
    
    print("\n📋 STEP 1: Gmail API Setup")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable the Gmail API")
    print("4. Go to 'Credentials' → 'Create Credentials' → 'OAuth client ID'")
    print("5. Select 'Desktop application' as application type")
    print("6. Download the JSON file and copy the values to gmail_credentials.json")
    
    print("\n📋 STEP 2: Outlook API Setup")
    print("1. Go to https://portal.azure.com/")
    print("2. Navigate to 'Azure Active Directory' → 'App registrations'")
    print("3. Click 'New registration'")
    print("4. Set redirect URI to 'http://localhost'")
    print("5. Go to 'API permissions' → 'Add a permission' → 'Microsoft Graph'")
    print("6. Select 'Mail.ReadWrite' permissions")
    print("7. Go to 'Certificates & secrets' → 'New client secret'")
    print("8. Copy values to outlook_credentials.json")
    
    print("\n📋 STEP 3: Run the Application")
    print("1. Update credentials files with your actual API keys")
    print("2. Run: python main.py")
    print("3. Connect your email accounts and start organizing!")
    
    print("\n🔧 Troubleshooting:")
    print("- If authentication fails, check API credentials are correct")
    print("- Ensure APIs are enabled in respective developer consoles")
    print("- Check that redirect URIs match your setup")
    print("- Verify you have granted all necessary permissions")

def main():
    """Main setup function"""
    print("🔧 Email Organizer Setup")
    print("="*40)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Create credential files if they don't exist
    if not os.path.exists('gmail_credentials.json'):
        create_gmail_credentials()
    else:
        print("✅ gmail_credentials.json already exists")
    
    if not os.path.exists('outlook_credentials.json'):
        create_outlook_credentials()
    else:
        print("✅ outlook_credentials.json already exists")
    
    # Check if credentials are configured
    gmail_configured = False
    outlook_configured = False
    
    try:
        with open('gmail_credentials.json', 'r') as f:
            gmail_data = json.load(f)
            if 'YOUR_GMAIL_CLIENT_ID_HERE' not in str(gmail_data):
                gmail_configured = True
    except:
        pass
    
    try:
        with open('outlook_credentials.json', 'r') as f:
            outlook_data = json.load(f)
            if 'YOUR_OUTLOOK_CLIENT_ID_HERE' not in str(outlook_data):
                outlook_configured = True
    except:
        pass
    
    print("\n📊 Configuration Status:")
    print(f"Gmail API: {'✅ Configured' if gmail_configured else '❌ Needs setup'}")
    print(f"Outlook API: {'✅ Configured' if outlook_configured else '❌ Needs setup'}")
    
    if gmail_configured and outlook_configured:
        print("\n🎉 Setup complete! You can now run the application:")
        print("   python main.py")
    else:
        print_setup_instructions()
    
    print("\n💡 Need help? Check the README.md file for detailed instructions")

if __name__ == "__main__":
    main()
