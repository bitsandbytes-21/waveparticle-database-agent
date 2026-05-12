"""Database adapter supporting SQLite and PostgreSQL"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Generator
import streamlit as st


class DatabaseAdapter:
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.environ.get("DATABASE_URL") or "characters.db"
        self.is_postgres = "postgresql" in self.connection_string.lower() or "postgres" in self.connection_string.lower()

    @contextmanager
    def get_connection(self):
        if self.is_postgres:
            from psycopg2.extras import RealDictCursor
            import psycopg2
            conn = psycopg2.connect(self.connection_string, cursor_factory=RealDictCursor)
        else:
            conn = sqlite3.connect(self.connection_string)
            conn.row_factory = sqlite3.Row

        try:
            yield conn
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.is_postgres:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS characters (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(500) NOT NULL,
                        resonance_types TEXT NOT NULL,
                        last_observed VARCHAR(500) NOT NULL,
                        echo TEXT NOT NULL,
                        character_task TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            else:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS characters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        resonance_types TEXT NOT NULL,
                        last_observed TEXT NOT NULL,
                        echo TEXT NOT NULL,
                        character_task TEXT DEFAULT '',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            conn.commit()

    def save_character(self, name: str, resonance_types: str, last_observed: str, echo: str, character_task: str = "") -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO characters (name, resonance_types, last_observed, echo, character_task)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """ if self.is_postgres else """
                INSERT INTO characters (name, resonance_types, last_observed, echo, character_task)
                VALUES (?, ?, ?, ?, ?)
            """, (name, resonance_types, last_observed, echo, character_task))
            conn.commit()
            if self.is_postgres:
                return cursor.fetchone()[0]
            return cursor.lastrowid

    def get_all_characters(self) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM characters ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def search_characters(self, query: str) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if self.is_postgres:
                cursor.execute(
                    "SELECT * FROM characters WHERE name ILIKE %s OR character_task ILIKE %s ORDER BY created_at DESC",
                    (f"%{query}%", f"%{query}%")
                )
            else:
                cursor.execute(
                    "SELECT * FROM characters WHERE name LIKE ? OR character_task LIKE ? ORDER BY created_at DESC",
                    (f"%{query}%", f"%{query}%")
                )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_character(self, character_id: int) -> Optional[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM characters WHERE id = %s" if self.is_postgres else
                          "SELECT * FROM characters WHERE id = ?", (character_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_character(self, character_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM characters WHERE id = %s" if self.is_postgres else
                          "DELETE FROM characters WHERE id = ?", (character_id,))
            conn.commit()


def get_db():
    if 'db_adapter' not in st.session_state:
        db_url = os.environ.get("DATABASE_URL") or st.secrets.get("DATABASE_URL", "characters.db")
        st.session_state.db_adapter = DatabaseAdapter(db_url)
        st.session_state.db_adapter.init_db()
    return st.session_state.db_adapter
