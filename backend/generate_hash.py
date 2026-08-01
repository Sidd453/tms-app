"""Fix admin password in DB. Usage: python generate_hash.py"""
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

load_dotenv()

PASSWORD = "Admin@123"
h = generate_password_hash(PASSWORD)
print(f"\nPassword : {PASSWORD}")
print(f"Hash     : {h[:40]}...\n")

MYSQL_HOST     = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT     = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER     = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "MySql@123")
MYSQL_DB       = os.getenv("MYSQL_DB", "tms_db")
MYSQL_USE_SSL  = os.getenv("MYSQL_USE_SSL", "false").lower() == "true"

try:
    import pymysql
    kwargs = dict(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                  password=MYSQL_PASSWORD, database=MYSQL_DB)
    if MYSQL_USE_SSL:
        kwargs["ssl"] = {}
    conn = pymysql.connect(**kwargs)
    cur  = conn.cursor()
    cur.execute("UPDATE users SET password_hash=%s WHERE official_email='purvaadmin@srujaninfotech.com'", (h,))
    conn.commit()
    rows = cur.rowcount; cur.close(); conn.close()
    if rows:
        print(f"[OK] Password updated!")
        print(f"    Email   : purvaadmin@srujaninfotech.com")
        print(f"    Password: Admin@123\n")
    else:
        print("[WARN] No rows updated - run init_db.sql first\n")
except Exception as e:
    print(f"[WARN] DB error: {e}")
    print(f"\nRun manually in MySQL:")
    print(f"USE tms_db; UPDATE users SET password_hash='{h}' WHERE official_email='purvaadmin@srujaninfotech.com';")
