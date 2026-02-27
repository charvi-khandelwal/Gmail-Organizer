# Contributing

Thanks for contributing to Gmail Organizer.

## Development setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Add local Gmail credentials (never commit secrets):

- `gmail_credentials.json`
- `gmail_token.pickle` (generated after auth)

3. Run locally:

```bash
python3 main.py
```

## Branching workflow

1. Create a feature branch from `main`.
2. Keep commits focused and descriptive.
3. Open a PR with:
   - what changed
   - why it changed
   - screenshots for UI changes

## Code style

- Keep changes focused and minimal.
- Follow existing naming/style patterns in `main.py` and `gmail_service.py`.
- Prefer small helper methods over large, repeated blocks.
- Preserve dark/light mode behavior when editing UI.

## Security & privacy

Never commit:

- `gmail_credentials.json`
- `gmail_token.pickle`
- local DB/cache artifacts

The project `.gitignore` already excludes these files.

## Testing checklist

Before pushing:

- App launches (`python3 main.py`)
- Gmail auth flow works
- Inbox/folder switching works
- Bulk delete actions work
- Light/dark mode toggle remains readable
