# EMS Deployment & Troubleshooting Guide

## Employee Management System (EMS)

This document records the problems encountered while moving the EMS database from Render/PostgreSQL to Supabase, deploying the Flask application to Render, and troubleshooting login/test credentials.

---

## 1. EMS Architecture

The current production setup is:

```text
User Browser
     |
     v
   Render
 Flask EMS
     |
     v
Supabase PostgreSQL
```

Employee images can be stored through Cloudinary when cloud storage is enabled.

The local development setup is:

```text
Local PC
   |
   v
Flask EMS
   |
   v
PostgreSQL / Supabase
```

---

# 2. Database Configuration

The Flask application reads the database connection from the environment:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
```

This means the database URL should not be hard-coded directly into `app.py`.

### Local `.env`

Example:

```text
DATABASE_URL=postgresql://username:password@host:port/database
```

The actual password must never be committed to GitHub.

### Render

For the deployed application, configure:

```text
Render
  -> EMS
  -> Environment
  -> DATABASE_URL
```

The value stored in Render should be the correct Supabase PostgreSQL connection string.

---

# 3. Important: Port 5432 vs Port 443

PostgreSQL normally uses:

```text
5432
```

HTTPS uses:

```text
443
```

During development, the office network was able to connect to port `443` but not to PostgreSQL port `5432`.

Example test:

```powershell
Test-NetConnection aws-0-ap-northeast-1.pooler.supabase.com -Port 5432
```

If the result is:

```text
TcpTestSucceeded : False
```

the computer/network cannot establish a TCP connection to that PostgreSQL port.

This can happen because of:

- Office firewall rules
- Network security policies
- Proxy restrictions
- ISP/network restrictions
- PostgreSQL port filtering

### Important

This does NOT automatically mean that Render cannot connect to Supabase.

The local computer and Render are different network environments.

```text
Office PC
   |
   +----> Supabase:5432
   |          |
   |          +----> May be blocked
   |
   +----> Render
              |
              +----> Supabase
                         |
                         +----> Can still work
```

Therefore, always test the actual deployed application through Render.

---

# 4. Supabase Hostname Error

One error encountered was:

```text
could not translate host name
```

Example:

```text
could not translate host name "db.xxxxx.supabase.co"
to address
```

This usually means the computer could not resolve the hostname through DNS.

Possible causes:

- Incorrect hostname
- Incorrect connection string
- DNS/network issue
- Supabase connection endpoint changed
- The endpoint is not reachable from the current network

First verify the connection string in Supabase.

Do not guess the hostname.

Use the connection information provided by Supabase.

---

# 5. Connection Refused Error

Another error was:

```text
connection to server at "aws-0-ap-northeast-1.pooler.supabase.com"
port 5432 failed:
Connection refused
```

This means the hostname resolved to an IP address, but the TCP connection to that port was not accepted.

Example:

```text
aws-0-ap-northeast-1.pooler.supabase.com
    |
    +---- 35.79.125.133:5432
    +---- 52.68.3.1:5432
    +---- 54.64.190.72:5432
```

The important distinction is:

### DNS problem

```text
could not translate host name
```

Hostname cannot be resolved.

### TCP connection problem

```text
Connection refused
```

Hostname was resolved, but the connection to the PostgreSQL port failed.

---

# 6. Testing PostgreSQL Connectivity

From Windows PowerShell:

```powershell
Test-NetConnection aws-0-ap-northeast-1.pooler.supabase.com -Port 5432
```

Look at:

```text
TcpTestSucceeded
```

### If:

```text
TcpTestSucceeded : True
```

The computer can establish a TCP connection to that endpoint/port.

### If:

```text
TcpTestSucceeded : False
```

The connection is not succeeding from that computer/network.

This test only tells you about the current machine/network.

It does not prove that Render has the same connectivity result.

---

# 7. Flask-Migrate and `upgrade()`

Flask-Migrate uses Alembic to apply database migrations.

Typical command:

```bash
flask db upgrade
```

The migration process needs to connect to the database.

The migration flow is:

```text
Flask-Migrate
      |
      v
    Alembic
      |
      v
SQLAlchemy
      |
      v
psycopg2
      |
      v
PostgreSQL
```

If PostgreSQL cannot be reached, migration will fail.

An error may appear inside:

```text
migrations/env.py
```

This does not necessarily mean `env.py` itself is broken.

It can simply mean that Alembic attempted to connect to the database and the connection failed.

---

# 8. Searching for `upgrade()` in the Project

If you are unsure whether `upgrade()` is being called manually, search the project.

Windows:

```cmd
findstr /S /N /I "upgrade()" *.py
```

This helps identify code such as:

```python
upgrade()
```

inside your application.

It also finds references inside installed packages.

### Important

Do not modify the `upgrade()` functions inside:

```text
.venv\
```

Those are package files.

Focus on your own project files, especially:

```text
app.py
migrations\
```

---

# 9. Flask Login Error: HTTP 500

After deployment, the EMS login page returned:

```text
500 Internal Server Error
```

The Render logs showed:

```text
ERROR in app: Exception on /login [POST]
```

The important part of the traceback was:

```text
ValueError: Invalid hash method '32768'
```

This happened while executing:

```python
check_password_hash(
    user.password,
    password
)
```

The login flow was:

```text
User enters username/password
            |
            v
Find user in database
            |
            v
check_password_hash()
            |
            v
Read stored password hash
            |
            v
Invalid hash method '32768'
            |
            v
HTTP 500
```

---

# 10. What `Invalid hash method '32768'` Means

This error is related to the format of the stored password hash and how the current Werkzeug installation interprets it.

It does NOT simply mean:

```text
Wrong password
```

If the password were simply wrong, `check_password_hash()` would normally return `False`.

Instead, the application raised an exception:

```text
ValueError
```

Therefore the application crashed while trying to interpret the stored hash.

---

# 11. Password Hashing in EMS

The application uses Werkzeug:

```python
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)
```

### Generate a password hash

```python
hashed_password = generate_password_hash(password)
```

### Verify a password

```python
check_password_hash(
    user.password,
    password
)
```

The database should contain the generated hash, not the plain-text password.

For example, do NOT store:

```text
admin123
```

as the value of the password column.

Instead, store a generated password hash.

---

# 12. Creating a New Test Account

When a test account is needed, generate a fresh password hash.

For a controlled test account, an explicit method can be used:

```python
hashed_password = generate_password_hash(
    'Test123!',
    method='pbkdf2:sha256'
)
```

Then:

```python
admin = User(
    username='testuser',
    password=hashed_password
)

db.session.add(admin)
db.session.commit()
```

Example test credentials:

```text
Username: testuser
Password: Test123!
```

These credentials are for testing only.

---

# 13. Temporary `/create-admin` Route

During development, a temporary route can be used to create a test user.

Example:

```python
@app.route('/create-admin')
def create_admin():

    existing_user = User.query.filter_by(
        username='testuser'
    ).first()

    if existing_user:
        return 'Test user already exists'

    hashed_password = generate_password_hash(
        'Test123!',
        method='pbkdf2:sha256'
    )

    admin = User(
        username='testuser',
        password=hashed_password
    )

    db.session.add(admin)
    db.session.commit()

    return 'Test User Created'
```

After deployment, visit:

```text
https://YOUR-RENDER-APP.onrender.com/create-admin
```

If successful:

```text
Test User Created
```

Then test:

```text
https://YOUR-RENDER-APP.onrender.com/login
```

with:

```text
Username: testuser
Password: Test123!
```

---

# 14. VERY IMPORTANT: Remove `/create-admin`

Do not leave a public account-creation route in production.

A route like:

```text
/create-admin
```

can be abused if it is publicly accessible.

After successfully creating the test account:

1. Remove the temporary route.
2. Commit the change.
3. Push to GitHub.
4. Let Render redeploy.
5. Confirm that the temporary route is no longer available.

---

# 15. Do Not Put Passwords in GitHub

Never commit:

```text
DATABASE_URL
DATABASE PASSWORD
SECRET_KEY
CLOUDINARY_API_SECRET
REAL USER PASSWORDS
```

to GitHub.

Use:

```text
.env
```

locally.

For Render, use:

```text
Render -> Environment Variables
```

---

# 16. Do Not Expose Environment Variables

Avoid leaving a production route such as:

```text
/env
```

that displays sensitive configuration.

Environment variables may contain:

- Database credentials
- Secret keys
- API keys
- Cloudinary credentials

If an `/env` debugging route was created during development, remove it before production deployment.

---

# 17. Render Troubleshooting Workflow

When the deployed EMS shows:

```text
500 Internal Server Error
```

do NOT immediately change the code.

Follow this process:

```text
1. Open Render
       |
       v
2. Open EMS service
       |
       v
3. Open Logs
       |
       v
4. Reproduce the error
       |
       v
5. Find "ERROR in app"
       |
       v
6. Read the traceback
       |
       v
7. Look at the LAST exception
       |
       v
8. Fix that specific problem
```

The last exception is usually much more useful than the first Flask error message.

---

# 18. Common Errors

## `OperationalError`

Example:

```text
sqlalchemy.exc.OperationalError
```

Usually investigate:

- Database URL
- Host
- Port
- Username
- Password
- Database availability
- Network connectivity

---

## `could not translate host name`

Usually investigate:

- Hostname
- DNS
- Connection string
- Network

---

## `Connection refused`

Usually investigate:

- Port
- Endpoint
- Firewall
- Network access
- Supabase connection endpoint

---

## `UndefinedTable`

Usually investigate:

- Database migrations
- Missing table
- Wrong database
- Wrong schema

---

## `IntegrityError`

Usually investigate:

- Duplicate username
- Duplicate unique value
- Foreign key violation
- NOT NULL constraint

---

## `Invalid hash method`

Usually investigate:

- Stored password hash
- Werkzeug version
- Password hash format
- How the user/password was originally created

Do not manually edit the hash string.

Generate a new valid hash instead.

---

# 19. Deployment Architecture Reminder

The deployed application works like this:

```text
                    INTERNET
                       |
                       v
                 +-----------+
                 |   Render  |
                 | Flask EMS |
                 +-----------+
                       |
                       |
                       v
                +-------------+
                |   Supabase  |
                | PostgreSQL  |
                +-------------+
```

The user's office computer does not need direct PostgreSQL access to use the deployed EMS.

The browser only needs to reach the Render website.

```text
Office PC
    |
    | HTTPS / 443
    v
 Render
    |
    | PostgreSQL connection
    v
 Supabase
```

Therefore, an office network blocking PostgreSQL port `5432` does not necessarily prevent the deployed application from working.

---

# 20. Quick Reference

### Local application

```bash
.venv\Scripts\activate
python app.py
```

### Test database connection

```powershell
Test-NetConnection YOUR_DATABASE_HOST -Port 5432
```

### Flask migration

```bash
flask db upgrade
```

### Render troubleshooting

```text
Render
 -> EMS
 -> Logs
```

### Login problem

Check the LAST exception in the traceback.

### Password problem

Use:

```python
generate_password_hash()
```

and:

```python
check_password_hash()
```

Do not store plain-text passwords.

---

# 21. Most Important Lessons

### Lesson 1

A `500 Internal Server Error` is only the symptom.

Always check the Render traceback for the actual exception.

### Lesson 2

`5432` is PostgreSQL.

`443` is HTTPS.

They serve different purposes.

### Lesson 3

A local office network problem does not necessarily mean Render has the same problem.

### Lesson 4

Never change random files when troubleshooting.

Identify the exact exception first.

### Lesson 5

Never manually edit password hashes.

Generate a new hash.

### Lesson 6

Temporary debugging routes such as:

```text
/create-admin
/env
/debug
```

should be removed or protected before production.

---

# 22. Emergency Checklist

If you forget what to do, follow these steps:

```text
[ ] Is the Render website running?
[ ] Check Render Logs.
[ ] Reproduce the error.
[ ] Find "ERROR in app".
[ ] Read the bottom of the traceback.
[ ] Identify the exception type.
[ ] If database error -> check DATABASE_URL/connection.
[ ] If password hash error -> create a new password hash.
[ ] If migration error -> check Flask-Migrate.
[ ] If office connection fails on 5432 -> test the network.
[ ] Do not change random code.
[ ] Do not expose secrets.
[ ] Remove temporary debugging routes before production.
```

---

# 23. Test Account Reminder

For development/testing only:

```text
Username: testuser
Password: Test123!
```

If this account is used in the future, keep the credentials in a private password manager or private development note rather than in GitHub.

---

# 24. Final Rule to Remember

When something breaks:

> **Don't guess. Check the logs, find the actual exception, then fix that specific problem.**

This was the most important lesson from the Supabase/Render deployment and login troubleshooting process.
