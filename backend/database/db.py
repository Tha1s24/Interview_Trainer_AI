import sqlite3
import os
from flask import g, current_app


def get_db():
    """
    Retorna a conexão SQLite para o contexto da requisição atual.
    Cria a conexão se ainda não existir no contexto Flask (g).
    """
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row  # Retorna linhas como dicionários
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Fecha a conexão ao final de cada requisição."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """
    Cria todas as tabelas a partir do schema.sql.
    Chamado uma vez na inicialização da aplicação.
    """
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    db_path = app.config["DATABASE_PATH"]

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")

    with open(schema_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())

    conn.commit()
    conn.close()
    print(f"[DB] Banco inicializado em: {db_path}")


def query(sql: str, params: tuple = (), one: bool = False):
    """
    Executa uma query SELECT e retorna uma ou várias linhas.

    Args:
        sql:    Query SQL com placeholders (?)
        params: Tupla de parâmetros
        one:    Se True, retorna apenas a primeira linha

    Returns:
        dict | list[dict] | None
    """
    cur = get_db().execute(sql, params)
    rv = cur.fetchall()
    return (dict(rv[0]) if rv else None) if one else [dict(row) for row in rv]


def execute(sql: str, params: tuple = ()):
    """
    Executa INSERT, UPDATE ou DELETE e faz commit.

    Returns:
        lastrowid do cursor
    """
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid