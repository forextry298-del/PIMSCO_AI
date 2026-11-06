from __future__ import annotations

import os
import re
import secrets
import sqlite3
import string
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(exist_ok=True)
DATABASE = Path(os.environ.get("PIMSCO_DATABASE", INSTANCE_DIR / "pimsco_ai.db"))

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("PIMSCO_SECRET_KEY", "local-demo-change-this-secret"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def create_tables() -> None:
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mobile TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            referral_code TEXT NOT NULL UNIQUE,
            referred_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (referred_by) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS invite_codes (
            code TEXT PRIMARY KEY,
            owner_id INTEGER,
            FOREIGN KEY (owner_id) REFERENCES users(id)
        );
        """
    )
    # A clearly documented starter code for local testing only.
    db.execute(
        "INSERT OR IGNORE INTO invite_codes (code, owner_id) VALUES (?, NULL)",
        ("PIMS1",),
    )
    db.commit()
    db.close()


def make_referral_code(db: sqlite3.Connection) -> str:
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(100):
        code = "P" + "".join(secrets.choice(alphabet) for _ in range(5))
        exists = db.execute("SELECT 1 FROM invite_codes WHERE code = ?", (code,)).fetchone()
        if not exists:
            return code
    raise RuntimeError("Could not create a unique invitation code")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "info")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    return redirect(url_for("dashboard" if session.get("user_id") else "login"))


@app.route("/signup", methods=["GET", "POST"])
@app.route("/register", methods=["GET", "POST"])
def signup():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        mobile = re.sub(r"\s+", "", request.form.get("mobile", ""))
        invite_code = request.form.get("invitation_code", "").strip().upper()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        accepted_terms = request.form.get("terms") == "on"

        if not re.fullmatch(r"0\d{9}", mobile):
            flash("Enter a valid 10-digit mobile number, for example 07XXXXXXXX.", "error")
        elif len(password) < 8:
            flash("Your password must contain at least 8 characters.", "error")
        elif password != confirm_password:
            flash("The passwords do not match.", "error")
        elif not accepted_terms:
            flash("Please agree to the Terms and Privacy Policy to continue.", "error")
        else:
            db = get_db()
            inviter = db.execute(
                "SELECT owner_id FROM invite_codes WHERE code = ?", (invite_code,)
            ).fetchone()
            if not inviter:
                flash("That invitation code was not found. Check it and try again.", "error")
            elif db.execute("SELECT 1 FROM users WHERE mobile = ?", (mobile,)).fetchone():
                flash("An account with that mobile number already exists. Please sign in.", "error")
            else:
                referral_code = make_referral_code(db)
                referred_by = inviter["owner_id"]
                try:
                    cursor = db.execute(
                        "INSERT INTO users (mobile, password_hash, referral_code, referred_by) VALUES (?, ?, ?, ?)",
                        (mobile, generate_password_hash(password), referral_code, referred_by),
                    )
                    user_id = cursor.lastrowid
                    db.execute(
                        "INSERT INTO invite_codes (code, owner_id) VALUES (?, ?)",
                        (referral_code, user_id),
                    )
                    db.commit()
                    session.clear()
                    session["user_id"] = user_id
                    flash("Your PIMSCO AI demo account is ready.", "success")
                    return redirect(url_for("dashboard"))
                except sqlite3.IntegrityError:
                    db.rollback()
                    flash("We could not create the account. Please try again.", "error")

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        mobile = re.sub(r"\s+", "", request.form.get("mobile", ""))
        password = request.form.get("password", "")
        user = get_db().execute("SELECT * FROM users WHERE mobile = ?", (mobile,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            flash("Welcome back.", "success")
            return redirect(url_for("dashboard"))
        flash("Mobile number or password is incorrect.", "error")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_db().execute(
        "SELECT id, mobile, referral_code, created_at FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()
    if not user:
        session.clear()
        return redirect(url_for("login"))
    referral_count = get_db().execute(
        "SELECT COUNT(*) AS total FROM users WHERE referred_by = ?", (user["id"],)
    ).fetchone()["total"]
    return render_template("dashboard.html", user=user, referral_count=referral_count)


@app.route("/forgot-password")
def forgot_password():
    flash("Password recovery is not configured in this local demo. Contact the site administrator.", "info")
    return redirect(url_for("login"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.route("/terms")
def terms():
    return render_template("info.html", page_title="Terms & Conditions", page_text="This is a local demonstration project. No payments, investments, or financial services are offered. Use test details only.")


@app.route("/privacy")
def privacy():
    return render_template("info.html", page_title="Privacy Policy", page_text="This demo stores mobile numbers and salted password hashes in a local SQLite database on the computer running it. Do not enter sensitive or real account credentials into a demo deployment.")


create_tables()

if __name__ == "__main__":
    # Local development only. Use a production WSGI server and a strong secret key before deployment.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)
