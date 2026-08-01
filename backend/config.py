import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # SECRET_KEY: falls back to the original hardcoded dev value so local
    # runs still work untouched; set a real one via env var in production.
    SECRET_KEY                  = os.getenv("SECRET_KEY", "tms-secret-2024-xK9mPqR7vB3nL8wQ-FIXED")
    MYSQL_HOST                  = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT                  = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER                  = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD              = os.getenv("MYSQL_PASSWORD", "MySql@123")
    MYSQL_DB                    = os.getenv("MYSQL_DB", "tms_db")
    # Set MYSQL_USE_SSL=true when connecting to a cloud MySQL that requires
    # SSL (e.g. Aiven) - local MySQL doesn't need this.
    MYSQL_USE_SSL                = os.getenv("MYSQL_USE_SSL", "false").lower() == "true"
    MYSQL_CURSORCLASS           = "DictCursor"
    BASE_DIR                    = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER               = os.path.join(BASE_DIR, "static", "uploads")
    MAX_CONTENT_LENGTH          = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS          = {"pdf","png","jpg","jpeg","gif","webp","doc","docx","xls","xlsx","txt","zip"}

    # Session cookies: same-origin locally (frontend served BY this same
    # Flask app on 127.0.0.1:5000) so Lax/insecure is fine there. Once
    # deployed behind HTTPS, set FLASK_ENV=production so the cookie still
    # works correctly (Secure required over HTTPS).
    IS_PRODUCTION                = os.getenv("FLASK_ENV") == "production"
    SESSION_COOKIE_HTTPONLY     = True
    SESSION_COOKIE_SAMESITE     = "Lax"
    SESSION_COOKIE_SECURE       = IS_PRODUCTION
    SESSION_COOKIE_NAME         = "tms_session"
    PERMANENT_SESSION_LIFETIME  = timedelta(hours=8)
