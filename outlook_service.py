"""
Outlook Service - Handles Microsoft Graph API authentication and email operations
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional

import msal
import requests

class OutlookService:
    def __init__(self):
        # Microsoft Graph API settings
        self.client_id = None
        self.client_secret = None
        self.authority = "https://login.microsoftonline.com/common"
        self.scope = ["https://graph.microsoft.com/Mail.ReadWrite"]
        
        # Authentication
        self.app = None
        self.access_token = None
        self.user_email = None
        
        # Credentials file
        self.credentials_path = 'outlook_credentials.json'
        
        # Load credentials if available
        self.load_credentials()
    
    def load_credentials(self):
        """Load Outlook credentials from file"""
        if os.path.exists(self.credentials_path):
            try:
                with open(self.credentials_path, 'r') as f:
                    creds = json.load(f)
                    self.client_id = creds.get('client_id')
                    self.client_secret = creds.get('client_secret')
            except Exception as e:
                print(f"Error loading credentials: {e}")
    
    def create_sample_credentials(self):
        """Create a sample credentials file with instructions"""
        sample_creds = {
            "client_id": "YOUR_CLIENT_ID_HERE",
            "client_secret": "YOUR_CLIENT_SECRET_HERE",
            "tenant_id": "YOUR_TENANT_ID_HERE (optional)"
        }
        
        with open(self.credentials_path, 'w') as f:
            json.dump(sample_creds, f, indent=2)
        
        print(f"Created sample credentials file: {self.credentials_path}")
        print("Please replace the placeholder values with actual values from Azure AD")
        print("Get these from Azure Portal: https://portal.azure.com/")
    
    def authenticate(self) -> bool:
        """Authenticate with Microsoft Graph API"""
        try:
            if not self.client_id or not self.client_secret:
                if not os.path.exists(self.credentials_path):
                    self.create_sample_credentials()
                return False
            
            # Initialize MSAL app
            self.app = msal.ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=self.authority
            )
            
            # Acquire token interactively
            result = self.app.acquire_token_for_client(scopes=self.scope)
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                
                # Get user info
                self.user_email = self.get_user_email()
                
                return True
            else:
                print(f"Authentication failed: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return self.access_token is not None
    
    def get_user_email(self) -> str:
        """Get authenticated user email"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get('mail') or user_data.get('userPrincipalName', '')
            else:
                print(f"Error getting user info: {response.status_code}")
                return ''
                
        except Exception as e:
            print(f"Error getting user email: {e}")
            return ''
    
    def get_emails(self, max_results: int = 50) -> List[Dict]:
        """Get list of emails from Outlook"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get messages from inbox
            url = f'https://graph.microsoft.com/v1.0/me/messages?$top={max_results}&$orderby=receivedDateTime desc'
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('value', [])
                
                emails = []
                for message in messages:
                    email_data = self.parse_outlook_message(message)
                    if email_data:
                        emails.append(email_data)
                
                return emails
            else:
                print(f"Error getting emails: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting emails: {e}")
            return []
    
    def parse_outlook_message(self, message: Dict) -> Optional[Dict]:
        """Parse Outlook message format"""
        try:
            # Extract sender information
            sender_info = message.get('from', {})
            sender_email = sender_info.get('emailAddress', {})
            sender = f"{sender_email.get('name', '')} <{sender_email.get('address', '')}>"
            
            # Clean up sender format
            if not sender_email.get('name'):
                sender = sender_email.get('address', 'Unknown')
            
            # Get subject and date
            subject = message.get('subject', 'No Subject')
            
            # Parse received date
            received_time = message.get('receivedDateTime', '')
            try:
                dt = datetime.fromisoformat(received_time.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_date = received_time
            
            # Get body preview (snippet)
            body_preview = message.get('bodyPreview', '')
            
            return {
                'id': message.get('id', ''),
                'sender': sender,
                'subject': subject,
                'date': formatted_date,
                'snippet': body_preview,
                'body': message.get('body', {}).get('content', ''),
                'isRead': message.get('isRead', False)
            }
            
        except Exception as e:
            print(f"Error parsing message: {e}")
            return None
    
    def delete_emails(self, message_ids: List[str]) -> int:
        """Delete multiple emails from Outlook"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            deleted_count = 0
            
            for message_id in message_ids:
                try:
                    url = f'https://graph.microsoft.com/v1.0/me/messages/{message_id}'
                    response = requests.delete(url, headers=headers)
                    
                    if response.status_code == 204:  # No Content = successful deletion
                        deleted_count += 1
                    else:
                        print(f"Error deleting message {message_id}: {response.status_code}")
                        
                except Exception as e:
                    print(f"Error deleting message {message_id}: {e}")
                    continue
            
            return deleted_count
            
        except Exception as e:
            print(f"Error in batch delete: {e}")
            return 0
    
    def search_emails(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search emails with query"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Use $search parameter for Outlook
            url = f'https://graph.microsoft.com/v1.0/me/messages?$search="{query}"&$top={max_results}&$orderby=receivedDateTime desc'
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('value', [])
                
                emails = []
                for message in messages:
                    email_data = self.parse_outlook_message(message)
                    if email_data:
                        emails.append(email_data)
                
                return emails
            else:
                print(f"Error searching emails: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error searching emails: {e}")
            return []
    
    def get_emails_by_sender(self, sender: str, max_results: int = 50) -> List[Dict]:
        """Get emails from specific sender"""
        # For Outlook, we can filter by sender email address
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Filter by sender email
            filter_query = f"from/emailAddress/address eq '{sender}'"
            url = f'https://graph.microsoft.com/v1.0/me/messages?$filter={filter_query}&$top={max_results}&$orderby=receivedDateTime desc'
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get('value', [])
                
                emails = []
                for message in messages:
                    email_data = self.parse_outlook_message(message)
                    if email_data:
                        emails.append(email_data)
                
                return emails
            else:
                # If filter fails, try search
                return self.search_emails(sender, max_results)
                
        except Exception as e:
            print(f"Error getting emails by sender: {e}")
            return []
    
    def mark_as_read(self, message_ids: List[str]) -> int:
        """Mark emails as read"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            modified_count = 0
            
            for message_id in message_ids:
                try:
                    url = f'https://graph.microsoft.com/v1.0/me/messages/{message_id}'
                    body = {'isRead': True}
                    
                    response = requests.patch(url, headers=headers, json=body)
                    
                    if response.status_code == 200:
                        modified_count += 1
                    else:
                        print(f"Error marking message {message_id} as read: {response.status_code}")
                        
                except Exception as e:
                    print(f"Error marking message {message_id} as read: {e}")
                    continue
            
            return modified_count
            
        except Exception as e:
            print(f"Error marking as read: {e}")
            return 0
    
    def mark_as_unread(self, message_ids: List[str]) -> int:
        """Mark emails as unread"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            modified_count = 0
            
            for message_id in message_ids:
                try:
                    url = f'https://graph.microsoft.com/v1.0/me/messages/{message_id}'
                    body = {'isRead': False}
                    
                    response = requests.patch(url, headers=headers, json=body)
                    
                    if response.status_code == 200:
                        modified_count += 1
                    else:
                        print(f"Error marking message {message_id} as unread: {response.status_code}")
                        
                except Exception as e:
                    print(f"Error marking message {message_id} as unread: {e}")
                    continue
            
            return modified_count
            
        except Exception as e:
            print(f"Error marking as unread: {e}")
            return 0
