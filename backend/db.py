"""
db.py - PyMySQL-backed drop-in replacement for flask-mysqldb.

Why: flask-mysqldb (MySQLdb/mysqlclient) needs a native C library
(libmysqlclient) to build, which frequently fails on Render's default
Python buildpack. PyMySQL is pure Python - it always installs cleanly,
and it's the same driver already proven working on Render+Aiven in our
other projects. app.py only ever calls qone()/qall()/exe() and does
mysql.init_app(app) - this file keeps that exact same surface so
nothing else needs to change.
"""
import pymysql
import pymysql.cursors


class _MySQLCompat:
    """Minimal stand-in for flask_mysqldb's `MySQL` extension object."""

    def __init__(self):
        self.app = None
        self._conn = None

    def init_app(self, app):
        self.app = app

    def _connect(self):
        cfg = self.app.config
        kwargs = dict(
            host=cfg["MYSQL_HOST"],
            port=int(cfg.get("MYSQL_PORT", 3306)),
            user=cfg["MYSQL_USER"],
            password=cfg["MYSQL_PASSWORD"],
            database=cfg["MYSQL_DB"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=False,
        )
        # Aiven (and most managed MySQL) require SSL; local MySQL doesn't.
        # An empty dict here is enough to turn TLS on for PyMySQL.
        if cfg.get("MYSQL_USE_SSL"):
            kwargs["ssl"] = {}
        return pymysql.connect(**kwargs)

    @property
    def connection(self):
        """Reuse one connection per process; transparently reconnect if
        it dropped (e.g. Aiven closed an idle connection)."""
        if self._conn is None:
            self._conn = self._connect()
        else:
            try:
                self._conn.ping(reconnect=True)
            except Exception:
                self._conn = self._connect()
        return self._conn


mysql = _MySQLCompat()


def get_cur():
    return mysql.connection.cursor()


def qone(sql, p=()):
    """Return one dict row or None."""
    try:
        c = get_cur()
        c.execute(sql, p)
        return c.fetchone()
    except Exception as e:
        print(f"[DB qone error] {e} | SQL: {sql}")
        return None


def qall(sql, p=()):
    """Return list of dict rows."""
    try:
        c = get_cur()
        c.execute(sql, p)
        return c.fetchall()
    except Exception as e:
        print(f"[DB qall error] {e} | SQL: {sql}")
        return []


def exe(sql, p=()):
    """Execute INSERT/UPDATE/DELETE, commit, return lastrowid. Raises on error."""
    c = get_cur()
    c.execute(sql, p)
    mysql.connection.commit()
    return c.lastrowid
