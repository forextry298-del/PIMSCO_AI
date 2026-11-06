# PIMSCO AI — Local Demo

A responsive Flask + SQLite demo based on the dark navy and electric-blue authentication style in the supplied screenshots. It includes signup, login, a simple dashboard, invitation codes, and logout.

**This is a local demo only.** It does not provide AI services, investments, deposits, withdrawals, payment processing, or real earnings. Use test details only.

## Run on Termux (Android)

```bash
pkg update -y
pkg install python zip -y
cd ~/PIMSCO_AI
python -m pip install -r requirements.txt
python app.py
```

Open this address in your phone browser:

```text
http://127.0.0.1:5000
```

To stop the server, press `CTRL + C` in Termux.

## First local signup

Use this starter invitation code:

```text
PIMS1
```

Create an account with a test Ugandan mobile format such as `0700000000` and a password of at least 8 characters. After registration, your dashboard displays a personal invitation code that another local test account can use.

## Included pages

- `/login` — sign in
- `/signup` or `/register` — create an account
- `/dashboard` — local demo dashboard and personal invitation code
- `/terms` and `/privacy` — demo policy information

## Data storage

The SQLite database is created automatically at `instance/pimsco_ai.db`. Delete that file to reset the local demo and restore the starter invitation code `PIMS1`.

## Before any public deployment

This project is intentionally configured for local testing. Before making it public, set a strong random `PIMSCO_SECRET_KEY`, use HTTPS, disable Flask debug mode, configure production hosting and database backups, and have the privacy/security design reviewed. Do not use it to collect sensitive personal information or money in its current form.

### Icons
The interface uses named Lucide icons (phone, ticket, lock, eye/eye-off) loaded from the Lucide CDN. An internet connection is needed for these icons to render; the rest of the app runs locally.
