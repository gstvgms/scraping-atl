# Módulo responsável por criar e gerenciar o banco de dados SQLite local

import sqlite3
from datetime import datetime
from config import DB_PATH


def init_db():
    """
    Inicializa o banco de dados criando as tabelas necessárias caso ainda não existam.
    Deve ser chamada antes de qualquer outra operação no banco.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Tabela principal com os posts coletados do Instagram
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            shortcode    TEXT UNIQUE,
            url          TEXT,
            date         TEXT,
            caption      TEXT,
            likes        INTEGER,
            comments     INTEGER,
            post_type    TEXT,
            collected_at TEXT
        )
    """)

    # Tabela de anotações feitas pela pesquisadora sobre cada post
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annotations (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            post_shortcode TEXT,
            annotation     TEXT,
            category       TEXT,
            relevant       INTEGER,
            updated_at     TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_post(post_data: dict):
    """
    Insere um post no banco de dados.
    Usa INSERT OR IGNORE para evitar duplicatas caso o coletor seja executado novamente.

    Parâmetros:
        post_data: dicionário com os campos do post
                   (shortcode, url, date, caption, likes, comments, post_type)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO posts
            (shortcode, url, date, caption, likes, comments, post_type, collected_at)
        VALUES
            (:shortcode, :url, :date, :caption, :likes, :comments, :post_type, :collected_at)
    """, {**post_data, "collected_at": datetime.now().isoformat()})

    conn.commit()
    conn.close()


def get_all_posts() -> list:
    """
    Retorna todos os posts armazenados no banco como uma lista de dicionários.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, shortcode, url, date, caption, likes, comments, post_type, collected_at
        FROM posts ORDER BY date DESC
    """)
    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return rows


def get_posts_by_keyword(keyword: str) -> list:
    """
    Retorna posts cuja legenda (caption) contém a palavra-chave informada.
    A busca é insensível a maiúsculas/minúsculas.

    Parâmetros:
        keyword: palavra ou expressão a buscar na legenda
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, shortcode, url, date, caption, likes, comments, post_type, collected_at
        FROM posts WHERE LOWER(caption) LIKE LOWER(?) ORDER BY date DESC
    """,
        (f"%{keyword}%",),
    )
    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return rows


def get_posts_by_date_range(start: str, end: str) -> list:
    """
    Retorna posts publicados dentro do intervalo de datas informado (inclusive).

    Parâmetros:
        start: data inicial no formato YYYY-MM-DD
        end:   data final no formato YYYY-MM-DD
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, shortcode, url, date, caption, likes, comments, post_type, collected_at
        FROM posts WHERE date BETWEEN ? AND ? ORDER BY date DESC
    """,
        (start, end),
    )
    rows = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return rows


def save_annotation(shortcode: str, annotation: str, category: str, relevant: int):
    """
    Salva ou atualiza a anotação da pesquisadora para um determinado post.
    Se já existir uma anotação para o shortcode, ela será substituída.

    Parâmetros:
        shortcode:  identificador único do post no Instagram
        annotation: texto livre com observações da pesquisadora
        category:   categoria atribuída (ex: "mobilização", "denúncia", "conquista")
        relevant:   1 se o post for relevante para a pesquisa, 0 caso contrário
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Verifica se já existe uma anotação para este post
    cursor.execute(
        "SELECT id FROM annotations WHERE post_shortcode = ?", (shortcode,)
    )
    existing = cursor.fetchone()

    now = datetime.now().isoformat()

    if existing:
        # Atualiza a anotação existente
        cursor.execute("""
            UPDATE annotations
            SET annotation = ?, category = ?, relevant = ?, updated_at = ?
            WHERE post_shortcode = ?
        """, (annotation, category, relevant, now, shortcode))
    else:
        # Insere nova anotação
        cursor.execute("""
            INSERT INTO annotations (post_shortcode, annotation, category, relevant, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (shortcode, annotation, category, relevant, now))

    conn.commit()
    conn.close()


def get_annotation(shortcode: str) -> dict | None:
    """
    Retorna a anotação de um post específico, ou None se não houver anotação.

    Parâmetros:
        shortcode: identificador único do post no Instagram
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, post_shortcode, annotation, category, relevant, updated_at
        FROM annotations WHERE post_shortcode = ?
    """, (shortcode,))
    row = cursor.fetchone()

    conn.close()
    return dict(row) if row else None
