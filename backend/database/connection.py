import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'interview.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas pelo nome
    return conn

def init_db():
    """Inicializa o banco de dados usando o schema.sql"""
    conn = get_db_connection()
    with open(os.path.join(os.path.dirname(__file__), 'schema.sql'), 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()