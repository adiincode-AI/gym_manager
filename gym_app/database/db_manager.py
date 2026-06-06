from __future__ import annotations

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Any

from .schema import SCHEMA
from .exceptions import (
    DatabaseError,
    RecordNotFoundError,
    DuplicateRecordError,
    TransactionError
)


class DatabaseManager:

    def __init__(self, db_path: str | None = None) -> None:
        base_dir = Path(__file__).resolve().parent.parent  # gym_app/
        default_db = base_dir / "database" / "gym.db"

        self.db_path = Path(db_path) if db_path else default_db

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        print("DB ACTUAL PATH:", self.db_path.resolve())

    def get_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        return connection

    def initialize_database(self) -> None:
        try:
            with self.get_connection() as conn:
                conn.executescript(SCHEMA)

        except sqlite3.Error as e:
            raise DatabaseError(
                f"Database initialization failed: {e}"
            ) from e

    @contextmanager
    def transaction(self):

        conn = self.get_connection()

        try:
            yield conn
            conn.commit()

        except Exception as e:
            conn.rollback()
            raise TransactionError(
                f"Transaction failed: {e}"
            ) from e

        finally:
            conn.close()

    def execute(
        self,
        query: str,
        params: tuple[Any, ...] = ()
    ) -> int:

        try:
            with self.transaction() as conn:
                cursor = conn.execute(query, params)
                return cursor.lastrowid

        except sqlite3.IntegrityError as e:
            raise DuplicateRecordError(str(e))

    def fetch_one(
        self,
        query: str,
        params: tuple[Any, ...] = ()
    ) -> dict | None:

        try:
            with self.get_connection() as conn:

                row = conn.execute(
                    query,
                    params
                ).fetchone()

                return dict(row) if row else None

        except sqlite3.Error as e:
            raise DatabaseError(str(e))

    def fetch_all(
        self,
        query: str,
        params: tuple[Any, ...] = ()
    ) -> list[dict]:

        try:
            with self.get_connection() as conn:

                rows = conn.execute(
                    query,
                    params
                ).fetchall()

                return [dict(row) for row in rows]

        except sqlite3.Error as e:
            raise DatabaseError(str(e))

    def execute_many(
        self,
        query: str,
        values: list[tuple]
    ) -> None:

        try:
            with self.transaction() as conn:
                conn.executemany(
                    query,
                    values
                )

        except sqlite3.Error as e:
            raise DatabaseError(str(e))

    def exists(
        self,
        query: str,
        params: tuple[Any, ...]
    ) -> bool:

        result = self.fetch_one(
            query,
            params
        )

        return result is not None

    def delete_by_id(
        self,
        table: str,
        record_id: int
    ) -> None:

        query = f"""
        DELETE FROM {table}
        WHERE id = ?
        """

        self.execute(
            query,
            (record_id,)
        )