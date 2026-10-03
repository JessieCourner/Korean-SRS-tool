import base64
import json
import re
import sqlite3
import time
from html import escape
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None


APP_DIR = Path(__file__).resolve().parent
# Resolve the database and lesson packs beside this script.  Streamlit Cloud
# can start the script with a working directory different from the repository
# root; relative paths then silently skipped the seed files and left an old
# database's card text on screen.
DB_PATH = APP_DIR / "korean_bunpro.db"
try:
    SUPABASE_DB_URL = st.secrets.get("SUPABASE_DB_URL", "")
except Exception:
    SUPABASE_DB_URL = ""


class CompatRow(dict):
    """A dict row that also supports SQLite-style numeric indexing."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


def postgres_sql(sql):
    sql = sql.replace("INSERT OR IGNORE INTO", "INSERT INTO")
    sql = sql.replace("INSERT OR REPLACE INTO settings", "INSERT INTO settings")
    sql = sql.replace("id INTEGER PRIMARY KEY AUTOINCREMENT", "id BIGSERIAL PRIMARY KEY")
    sql = sql.replace("AUTOINCREMENT", "")
    sql = sql.replace("?", "%s")
    if "INSERT INTO settings" in sql and "ON CONFLICT" not in sql:
        sql = sql.rstrip().rstrip(';') + " ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value"
    elif "INSERT INTO" in sql and "ON CONFLICT" not in sql and "INSERT OR" not in sql:
        # INSERT OR IGNORE was normalized above; this marker is added by the
        # cursor for those statements so ordinary inserts remain unchanged.
        pass
    return sql


class PostgresCursor:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = connection.raw.cursor(cursor_factory=RealDictCursor)
        connection._open_cursors.add(self)
        self.ignore_conflict = False

    def execute(self, sql, params=()):
        self.ignore_conflict = "INSERT OR IGNORE INTO" in sql
        transformed = postgres_sql(sql)
        if self.ignore_conflict and "ON CONFLICT" not in transformed:
            transformed = transformed.rstrip().rstrip(';') + " ON CONFLICT DO NOTHING"
        if transformed.lstrip().upper().startswith("PRAGMA TABLE_INFO"):
            table = re.search(r"PRAGMA TABLE_INFO\(([^)]+)\)", transformed, re.I).group(1).strip()
            transformed = "SELECT ordinal_position AS cid, column_name AS name FROM information_schema.columns WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position"
            params = (table,)
        try:
            self.cursor.execute(transformed, params)
        except Exception:
            # A failed PostgreSQL statement aborts the whole transaction.  If
            # the same Streamlit session reuses its connection, roll it back
            # immediately so the next button click can still work.
            self.connection.raw.rollback()
            raise
        # Bootstrap runs a deliberately large, single migration transaction
        # (all lesson/card packs must be synchronized together).  Mark the
        # connection as active after every successful statement so the
        # liveness guard cannot mistake that long transaction for an idle
        # socket and reconnect halfway through it.  Reconnecting there would
        # roll back the first lessons and make verify_live_card_content report
        # a misleading card_missing error.
        self.connection.last_used = time.monotonic()
        return self

    def executescript(self, sql):
        self.cursor.execute(postgres_sql(sql))
        return self

    def fetchone(self):
        try:
            row = self.cursor.fetchone()
