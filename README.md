# Email Organizer

A powerful macOS desktop application for managing Gmail and Outlook emails efficiently. This app simplifies email organization by allowing you to sort emails by sender, perform batch deletions, and manage multiple email accounts from one interface.

## Features

### Core Functionality
- **Multi-account support**: Connect to both Gmail and Outlook accounts
- **Batch operations**: Delete multiple emails at once instead of selecting individually
- **Sender-based organization**: Automatically groups emails by sender for easy management
- **Search and filter**: Find emails quickly by sender, subject, or content
- **Modern interface**: Clean, intuitive macOS-style interface

### Advanced Features
- **Email preview**: Double-click any email to preview its full content
- **Smart sorting**: Sort emails by sender, date, or subject
- **Account switching**: Easily switch between connected accounts
- **Visual grouping**: Color-coded emails by sender for quick identification
- **Bulk actions**: Clear all emails from a specific sender with one click
- **Persistent storage**: Saves account connections and settings locally

## Installation

### Prerequisites
- Python 3.7 or higher
- macOS 10.12 or later

### Setup Instructions

1. **Clone or download this repository**
   ```bash
   cd "/Users/swatik./Documents/GitHub/Email Organizer"
   ```

2. **Install required dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up Gmail API credentials**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Gmail API
   - Create OAuth 2.0 credentials (Desktop Application)
   - Download the credentials file and rename it to `gmail_credentials.json`
   - Replace the placeholder values in the file with your actual credentials

4. **Set up Outlook API credentials**
   - Go to [Azure Portal](https://portal.azure.com/)
   - Create a new App Registration
   - Add Microsoft Graph permissions (Mail.ReadWrite)
   - Create a client secret
   - Update `outlook_credentials.json` with your credentials

5. **Run the application**
   ```bash
   python main.py
   ```

## Usage

### Connecting Accounts

1. **Gmail Setup**
   - Click "Connect Gmail" button
   - Complete OAuth authentication in browser
   - Grant necessary permissions
   - Account will appear as connected

2. **Outlook Setup**
   - Click "Connect Outlook" button
   - Complete authentication process
   - Grant necessary permissions
   - Account will appear as connected

### Managing Emails

1. **View Emails**
   - Select an account from the dropdown
   - Emails will load automatically
   - Emails are color-coded by sender

2. **Select Emails**
   - Click checkbox column to select/deselect individual emails
   - Use "Select All" to select all visible emails
   - Use "Deselect All" to clear selections

3. **Delete Emails**
   - Select emails you want to delete
   - Click "Delete Selected" button
   - Confirm deletion in dialog
   - Progress will be shown in status bar

4. **Clear by Sender**
   - Click "Clear All" button
   - Select sender from list
   - Confirm to delete all emails from that sender

5. **Search and Filter**
   - Use search box to filter by sender, subject, or content
   - Use sort dropdown to change email order
   - Results update automatically

6. **Preview Emails**
   - Double-click any email to open preview window
   - Shows full email content and details

## Configuration Files

### gmail_credentials.json
```json
{
  "installed": {
    "client_id": "your_gmail_client_id",
    "client_secret": "your_gmail_client_secret",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "redirect_uris": ["http://localhost"]
  }
}
```

### outlook_credentials.json
```json
{
  "client_id": "your_outlook_client_id",
  "client_secret": "your_outlook_client_secret",
  "tenant_id": "your_tenant_id (optional)"
}
```

## Security

- **OAuth Authentication**: Uses secure OAuth 2.0 for both Gmail and Outlook
- **Local Storage**: Credentials stored locally using secure token storage
- **Minimal Permissions**: Requests only necessary email permissions
- **No Data Collection**: All data stays on your local machine

## Troubleshooting

### Common Issues

1. **"Failed to authenticate"**
   - Check that credentials files are properly configured
   - Ensure API access is enabled in respective developer consoles
   - Verify redirect URIs match your setup

2. **"No emails loaded"**
   - Check internet connection
   - Verify account permissions include email access
   - Try refreshing the connection

3. **"Delete operation failed"**
   - Ensure you have delete permissions for the account
   - Check if emails are already deleted
   - Verify API quota limits

### Getting Help

1. Check the console output for detailed error messages
2. Verify API credentials are correct and active
3. Ensure all required permissions are granted
4. Check internet connection and firewall settings

## Development

### Project Structure
```
Email Organizer/
├── main.py              # Main application GUI
├── gmail_service.py     # Gmail API integration
├── outlook_service.py   # Outlook API integration
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── gmail_credentials.json   # Gmail API credentials (create this)
├── outlook_credentials.json # Outlook API credentials (create this)
└── email_organizer.db   # Local database (created automatically)
```

### Dependencies
- `google-api-python-client`: Gmail API access
- `google-auth-oauthlib`: Gmail authentication
- `msal`: Microsoft authentication
- `requests`: HTTP requests for Outlook API
- `tkinter`: GUI framework (built into Python)

## License

This project is for personal use. Please respect the terms of service of Google and Microsoft APIs.

## Support

For issues and questions:
1. Check this README for common solutions
2. Review the console output for error details
3. Verify API setup in respective developer consoles

---

**Note**: This application requires proper API credentials setup. Follow the installation instructions carefully to ensure proper functionality.
