"""Database access layer."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import mysql.connector
from mysql.connector.cursor import MySQLCursor

from app.config import db
from app.logging_utils import log_error


@contextmanager
def db_cursor(*, dictionary: bool = False) -> Iterator[MySQLCursor]:
    connection = mysql.connector.connect(**db.as_kwargs())
    cursor = connection.cursor(dictionary=dictionary)
    try:
        yield cursor
        connection.commit()
    except mysql.connector.Error as err:
        log_error(f"Database error: {err}")
        connection.rollback()
        raise
    finally:
        try:
            cursor.close()
        finally:
            connection.close()


@contextmanager
def db_connection() -> Iterator[mysql.connector.MySQLConnection]:
    connection = mysql.connector.connect(**db.as_kwargs())
    try:
        yield connection
        connection.commit()
    except mysql.connector.Error as err:
        log_error(f"Database error: {err}")
        connection.rollback()
        raise
    finally:
        connection.close()
