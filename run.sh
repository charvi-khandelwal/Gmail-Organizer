#!/bin/bash

# Email Organizer Launch Script
# This script sets up the environment and launches the Email Organizer app

echo "🚀 Starting Email Organizer..."

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: main.py not found. Please run this script from the Email Organizer directory."
    exit 1
fi

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.7 or higher from https://www.python.org/"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import googleapiclient, msal, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing dependencies..."
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to install dependencies"
        exit 1
    fi
fi

# Check if credentials files exist
if [ ! -f "gmail_credentials.json" ]; then
    echo "⚠️  Warning: Gmail credentials file not found. Running setup..."
    python3 setup.py
    echo ""
    echo "Please update the gmail_credentials.json file with your API keys and run this script again."
    exit 1
fi

# Check if credentials are configured
echo "🔑 Checking credentials..."
python3 -c "
import json
try:
    with open('gmail_credentials.json', 'r') as f:
        gmail = json.load(f)
        if 'YOUR_GMAIL_CLIENT_ID_HERE' in str(gmail) or 'YOUR_GMAIL_CLIENT_SECRET_HERE' in str(gmail):
            print('❌ Gmail credentials not configured')
            exit(1)
except:
    print('❌ Error reading gmail_credentials.json')
    exit(1)

print('✅ Gmail credentials configured')
"

if [ $? -ne 0 ]; then
    echo ""
    echo "Please configure your API credentials in gmail_credentials.json"
    echo ""
    echo "See README.md for detailed setup instructions."
    exit 1
fi

# Launch the application
echo "🎯 Launching Email Organizer..."
python3 main.py
