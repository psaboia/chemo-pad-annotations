# Authentication Setup

The ChemoPAD Annotation Matcher includes session-based password authentication.

## Default Configuration

- **Default Password**: `chemopad2024`
- **Session Timeout**: 30 minutes of inactivity
- **Cookie Security**: HTTPOnly (prevents JavaScript access)

## Changing the Password

To use a different password, set the `CHEMOPAD_PASSWORD` environment variable:

```bash
export CHEMOPAD_PASSWORD="your-secure-password"
cd flask-app
uv run python -c "import app; app.app.run(host='127.0.0.1', port=5001)"
```

Or if running with gunicorn (production):

```bash
CHEMOPAD_PASSWORD="your-secure-password" gunicorn -w 1 -b 0.0.0.0:8080 app:app
```

## How It Works

1. **Login Page**: User visits the app and is redirected to `/login`
2. **Password Verification**: User enters password, which is checked against `PASSWORD` env var
3. **Session Creation**: On successful login, a session cookie is created
4. **Session Timeout**: Sessions expire after 30 minutes of inactivity
5. **Logout**: Users can click "Logout" in the navigation bar to clear their session

## Features

- ✅ Simple password-based authentication
- ✅ Session-based (no database required)
- ✅ Automatic 30-minute timeout
- ✅ HTTPOnly cookies (secure)
- ✅ All routes protected except login page

## Session Refresh

Sessions automatically refresh on each request. This means:
- User activity extends the session timeout
- 30-minute timer resets with each page view or API call
- User will be logged out if idle for 30 minutes

## Example Deployment

For the VM deployment at `http://pad-annotation.crc.nd.edu:8080/`:

```bash
#!/bin/bash
export CHEMOPAD_PASSWORD="your-vm-password"
cd /path/to/chemo-pad-annotations/flask-app
gunicorn -w 2 -b 0.0.0.0:8080 app:app &
```

## Security Notes

- Password is stored as plain text in environment variable
- For better security in production, consider:
  - Using HTTPS (set `SESSION_COOKIE_SECURE = True`)
  - Rotating passwords regularly
  - Using a secret management system
  - Implementing password hashing if multiple users needed
