"""
Gmail Service - Handles Gmail API authentication and email operations
"""

import os
import json
import pickle
import base64
from datetime import datetime
from typing import List, Dict, Optional

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class GmailService:
    def __init__(self):
        self.SCOPES = [
            'https://www.googleapis.com/auth/gmail.modify',
            'https://www.googleapis.com/auth/gmail.send',
        ]
        self.creds = None
        self.service = None
        self.user_email = None
        
        # Token storage path
        self.token_path = 'gmail_token.pickle'
        self.credentials_path = 'gmail_credentials.json'
        
        # Load credentials if available
        self.load_credentials()
    
    def load_credentials(self):
        """Load stored credentials if available"""
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)
    
    def save_credentials(self):
        """Save credentials to file"""
        with open(self.token_path, 'wb') as token:
            pickle.dump(self.creds, token)
    
    def authenticate(self) -> bool:
        """Authenticate with Gmail API"""
        try:
            # Check if we have valid credentials
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    # For development, create a simple credentials file
                    if not os.path.exists(self.credentials_path):
                        self.create_sample_credentials()
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                self.save_credentials()
            
            # Build the service
            self.service = build('gmail', 'v1', credentials=self.creds)
            
            # Get user email
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile['emailAddress']
            
            return True
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def create_sample_credentials(self):
        """Create a sample credentials file with instructions"""
        sample_creds = {
            "installed": {
                "client_id": "YOUR_CLIENT_ID_HERE",
                "client_secret": "YOUR_CLIENT_SECRET_HERE",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost"]
            }
        }
        
        with open(self.credentials_path, 'w') as f:
            json.dump(sample_creds, f, indent=2)
        
        print(f"Created sample credentials file: {self.credentials_path}")
        print("Please replace YOUR_CLIENT_ID_HERE and YOUR_CLIENT_SECRET_HERE with actual values")
        print("Get these from Google Cloud Console: https://console.cloud.google.com/")
    
    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return self.service is not None and self.creds is not None and self.creds.valid
    
    def get_user_email(self) -> str:
        """Get authenticated user email"""
        return self.user_email
    
    def get_emails(self, max_results: int = 50) -> List[Dict]:
        """Get list of emails"""
        return self._get_messages_with_filters(max_results=max_results)

    def _list_message_ids(
        self,
        label_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        max_results: int = 200,
    ) -> List[str]:
        """List message IDs with pagination."""
        message_ids: List[str] = []
        page_token = None

        while len(message_ids) < max_results:
            params = {
                'userId': 'me',
                'maxResults': min(500, max_results - len(message_ids)),
            }
            if label_ids:
                params['labelIds'] = label_ids
            if query:
                params['q'] = query
            if page_token:
                params['pageToken'] = page_token

            result = self.service.users().messages().list(**params).execute()
            messages = result.get('messages', [])
            message_ids.extend([m['id'] for m in messages])

            page_token = result.get('nextPageToken')
            if not page_token or not messages:
                break

        return message_ids[:max_results]

    def _get_messages_with_filters(
        self,
        label_ids: Optional[List[str]] = None,
        query: Optional[str] = None,
        max_results: int = 200,
    ) -> List[Dict]:
        """Fetch detailed message objects by labels/query."""
        try:
            message_ids = self._list_message_ids(
                label_ids=label_ids,
                query=query,
                max_results=max_results,
            )

            emails = []
            for message_id in message_ids:
                email_data = self.get_email_details(message_id)
                if email_data:
                    emails.append(email_data)

            return emails
            
        except HttpError as e:
            print(f"Error getting emails: {e}")
            return []
    
    def get_email_details(self, message_id: str) -> Optional[Dict]:
        """Get detailed email information"""
        try:
            message = self.service.users().messages().get(
                userId='me', id=message_id, format='metadata').execute()
            
            headers = message['payload'].get('headers', [])
            
            # Extract relevant headers
            sender = subject = date = ''
            for header in headers:
                if header['name'].lower() == 'from':
                    sender = header['value']
                elif header['name'].lower() == 'subject':
                    subject = header['value']
                elif header['name'].lower() == 'date':
                    date = header['value']
            
            # Get snippet
            snippet = message.get('snippet', '')
            
            # Parse date to more readable format
            try:
                from email.utils import parsedate_to_datetime
                dt = parsedate_to_datetime(date)
                formatted_date = dt.strftime('%Y-%m-%d %H:%M')
            except:
                formatted_date = date
            
            return {
                'id': message_id,
                'sender': sender,
                'subject': subject,
                'date': formatted_date,
                'snippet': snippet,
                'threadId': message.get('threadId', ''),
                'isRead': 'UNREAD' not in message.get('labelIds', []),
                'labelIds': message.get('labelIds', []),
            }
            
        except HttpError as e:
            print(f"Error getting email details: {e}")
            return None
    
    def delete_emails(self, message_ids: List[str]) -> int:
        """Delete multiple emails"""
        try:
            deleted_count = 0
            
            # Gmail API allows batch deletion
            for message_id in message_ids:
                try:
                    self.service.users().messages().delete(
                        userId='me', id=message_id).execute()
                    deleted_count += 1
                except HttpError as e:
                    print(f"Error deleting message {message_id}: {e}")
                    continue
            
            return deleted_count
            
        except Exception as e:
            print(f"Error in batch delete: {e}")
            return 0
    
    def search_emails(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search emails with query"""
        return self._get_messages_with_filters(query=query, max_results=max_results)
    
    def get_emails_by_sender(self, sender: str, max_results: int = 50) -> List[Dict]:
        """Get emails from specific sender"""
        query = f"from:{sender}"
        return self.search_emails(query, max_results)
    
    def mark_as_read(self, message_ids: List[str]) -> int:
        """Mark emails as read"""
        try:
            modified_count = 0
            
            for message_id in message_ids:
                try:
                    self.service.users().messages().modify(
                        userId='me', id=message_id,
                        body={'removeLabelIds': ['UNREAD']}).execute()
                    modified_count += 1
                except HttpError as e:
                    print(f"Error marking message {message_id} as read: {e}")
                    continue
            
            return modified_count
            
        except Exception as e:
            print(f"Error marking as read: {e}")
            return 0
    
    def get_sent_emails(self, max_results: int = 50) -> List[Dict]:
        """Get sent emails"""
        return self._get_messages_with_filters(label_ids=['SENT'], max_results=max_results)

    def get_snoozed_emails(self, max_results: int = 50) -> List[Dict]:
        """Get snoozed emails."""
        return self._get_messages_with_filters(label_ids=['SNOOZED'], max_results=max_results)
    
    def get_draft_emails(self, max_results: int = 50) -> List[Dict]:
        """Get draft emails"""
        try:
            result = self.service.users().drafts().list(
                userId='me', maxResults=max_results).execute()
            drafts = result.get('drafts', [])
            
            emails = []
            for draft in drafts:
                message_id = draft['message']['id']
                email_data = self.get_email_details(message_id)
                if email_data:
                    email_data['isDraft'] = True
                    emails.append(email_data)
            
            return emails
            
        except HttpError as e:
            print(f"Error getting draft emails: {e}")
            return []
    
    def get_starred_emails(self, max_results: int = 50) -> List[Dict]:
        """Get starred emails"""
        emails = self._get_messages_with_filters(label_ids=['STARRED'], max_results=max_results)
        for email in emails:
            email['isStarred'] = True
        return emails
    
    def get_trash_emails(self, max_results: int = 50) -> List[Dict]:
        """Get trash emails"""
        emails = self._get_messages_with_filters(label_ids=['TRASH'], max_results=max_results)
        for email in emails:
            email['isTrashed'] = True
        return emails

    def get_all_mail(self, max_results: int = 200) -> List[Dict]:
        """Get all mail messages."""
        return self._get_messages_with_filters(max_results=max_results)

    def get_important_emails(self, max_results: int = 200) -> List[Dict]:
        """Get important emails."""
        return self._get_messages_with_filters(label_ids=['IMPORTANT'], max_results=max_results)

    def get_attachment_emails(self, max_results: int = 200) -> List[Dict]:
        """Get emails that contain attachments."""
        return self._get_messages_with_filters(query='has:attachment', max_results=max_results)

    def get_email_body(self, message_id: str) -> str:
        """Fetch full email body for a message ID."""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full',
            ).execute()
            payload = message.get('payload', {})

            def decode_part(data: str) -> str:
                if not data:
                    return ''
                return base64.urlsafe_b64decode(data.encode('utf-8')).decode('utf-8', errors='ignore')

            body_data = payload.get('body', {}).get('data')
            if body_data:
                return decode_part(body_data)

            for part in payload.get('parts', []):
                mime_type = part.get('mimeType', '')
                if mime_type in ('text/plain', 'text/html'):
                    part_data = part.get('body', {}).get('data')
                    if part_data:
                        return decode_part(part_data)

            return message.get('snippet', '')
        except Exception as e:
            print(f"Error getting email body: {e}")
            return ''
    
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email"""
        try:
            message = {
                'raw': base64.urlsafe_b64encode(
                    f"To: {to}\nSubject: {subject}\n\n{body}".encode()
                ).decode()
            }
            
            result = self.service.users().messages().send(
                userId='me', body=message).execute()
            
            return True
            
        except HttpError as e:
            print(f"Error sending email: {e}")
            return False
