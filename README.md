# Gmail Organizer

Gmail Organizer is a macOS desktop app (Python + Tkinter) that gives you a Gmail-like inbox with fast bulk cleanup tools.

It focuses on **organizing and deleting emails at scale** while keeping familiar Gmail aesthetics.

## What it does

- Gmail-like inbox UI (light/dark adaptive)
- Folder navigation (Inbox, Sent, Drafts, Starred, Snoozed, Trash, All Mail, Important, Attachments)
- Category tabs (Primary / Promotions / Social)
- Batch operations:
  - select all
  - delete selected
  - clear all from sender
- Search, sort, and preview message content
- Compose + send + reply + forward

## Quick start

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Add Gmail API credentials

Create `gmail_credentials.json` in the project root:

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

### 3) Run

```bash
python3 main.py
```

## Gmail API setup checklist

In Google Cloud Console:

1. Create/select project
2. Enable **Gmail API**
3. Configure OAuth consent screen (Testing is fine)
4. Add your email under **Test users**
5. Create OAuth client ID for **Desktop app**
6. Put client ID/secret in `gmail_credentials.json`

## Security notes

- Do **not** commit credentials or tokens.
- `.gitignore` excludes:
  - `gmail_credentials.json`
  - `gmail_token.pickle`
  - local DB/cache artifacts

## Project structure

```text
Gmail-Organizer/
├── main.py
├── gmail_service.py
├── requirements.txt
├── run.sh
├── setup.py
├── README.md
└── CONTRIBUTING.md
```

## Troubleshooting

- **App not authorized (403 access_denied)**:
  - add your account in OAuth consent screen → Test users
- **Auth prompt doesn’t refresh after scope changes**:
  - delete `gmail_token.pickle` and re-authenticate
- **No emails shown**:
  - confirm Gmail API enabled and app has mailbox permission

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).
