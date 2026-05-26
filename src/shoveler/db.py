import duckdb
import os
import time
from typing import Literal, TypeAlias, TypedDict


QueryRow: TypeAlias = tuple[object, ...]


class QueryResult(TypedDict):
    columns: list[str]
    rows: list[QueryRow]
    elapsed: float
    error: str | None


class Database:
    def __init__(self):
        self.conn = None
        self.mode: Literal["file", "memory"] | None = None
        self.path: str | None = None

    def open_file(self, path: str):
        self._close_existing()
        self.conn = duckdb.connect(path)
        self.mode = "file"
        self.path = path

    def new_memory(self):
        self._close_existing()
        self.conn = duckdb.connect(":memory:")
        self.mode = "memory"
        self.path = None

    def checkpoint(self):
        if self.mode == "file" and self.conn:
            self.conn.execute("CHECKPOINT")

    def save_as(self, path: str) -> str:
        if not self.conn:
            raise RuntimeError("No database connected.")

        target_path = os.path.abspath(path)
        if self.mode == "file" and self.path and os.path.abspath(self.path) == target_path:
            self.checkpoint()
            return target_path

        source_catalog = self.conn.execute("PRAGMA database_list").fetchone()[1]
        source_catalog_escaped = source_catalog.replace('"', '""')
        target_path_escaped = target_path.replace("'", "''")
        target_catalog = "shoveler_save_target"

        self.conn.execute(f"ATTACH '{target_path_escaped}' AS {target_catalog}")
        try:
            self.conn.execute(
                f'COPY FROM DATABASE "{source_catalog_escaped}" TO {target_catalog}'
            )
        finally:
            self.conn.execute(f"DETACH {target_catalog}")

        self.open_file(target_path)
        return target_path

    @staticmethod
    def _build_result(
        columns: list[str], rows: list[QueryRow], elapsed: float, error: str | None
    ) -> QueryResult:
        return {
            "columns": columns,
            "rows": rows,
            "elapsed": elapsed,
            "error": error,
        }

    def execute(self, sql: str) -> QueryResult:
        """Return a query result with columns, rows, elapsed seconds, and error."""
        if not self.conn:
            return self._build_result([], [], 0.0, "No database connected.")
        start = time.perf_counter()
        try:
            result = self.conn.execute(sql)
            elapsed = time.perf_counter() - start
            if result.description:
                columns = [desc[0] for desc in result.description]
                rows = result.fetchall()
            else:
                columns = []
                rows = []
            return self._build_result(columns, rows, elapsed, None)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return self._build_result([], [], elapsed, str(e))

    def get_tables(self) -> list[str]:
        if not self.conn:
            return []
        try:
            result = self.conn.execute("SHOW TABLES").fetchall()
            return [row[0] for row in result]
        except Exception:
            return []

    def get_columns(self, table: str) -> list[tuple[str, str]]:
        if not self.conn:
            return []
        try:
            # DESCRIBE returns: column_name, column_type, null, key, default, extra
            result = self.conn.execute(f"DESCRIBE {table}").fetchall()
            return [(row[0], row[1]) for row in result]
        except Exception:
            return []

    def get_column_key_flags(self, table: str) -> dict[str, tuple[bool, bool]]:
        """Return key flags by column name as (is_primary_key, is_foreign_key)."""
        key_info = self.get_column_key_info(table)
        return {
            column: (details["is_primary_key"], details["referenced_table"] is not None)
            for column, details in key_info.items()
        }

    def get_column_key_info(self, table: str) -> dict[str, dict[str, bool | str | None]]:
        """Return per-column key metadata including referenced table for foreign keys."""
        if not self.conn:
            return {}

        pk_columns: set[str] = set()
        fk_columns: dict[str, str | None] = {}

        try:
            pk_result = self.conn.execute(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_catalog = kcu.constraint_catalog
                 AND tc.constraint_schema = kcu.constraint_schema
                 AND tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = current_schema()
                  AND tc.table_name = ?
                  AND tc.constraint_type = 'PRIMARY KEY'
                """,
                [table],
            ).fetchall()
            pk_columns = {row[0] for row in pk_result}
        except Exception:
            escaped_table = table.replace("'", "''")
            try:
                pragma_result = self.conn.execute(
                    f"PRAGMA table_info('{escaped_table}')"
                ).fetchall()
                for row in pragma_result:
                    if len(row) > 5 and row[5]:
                        pk_columns.add(row[1])
            except Exception:
                pass

        try:
            fk_result = self.conn.execute(
                """
                SELECT UNNEST(constraint_column_names) AS column_name, referenced_table
                FROM duckdb_constraints()
                WHERE schema_name = current_schema()
                  AND table_name = ?
                  AND constraint_type = 'FOREIGN KEY'
                """,
                [table],
            ).fetchall()
            fk_columns = {row[0]: row[1] for row in fk_result}
        except Exception:
            pass

        return {
            column: {
                "is_primary_key": column in pk_columns,
                "referenced_table": fk_columns.get(column),
            }
            for column, _ in self.get_columns(table)
        }

    def _close_existing(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def close(self):
        self._close_existing()
        self.mode = None
        self.path = None

    @property
    def is_connected(self) -> bool:
        return self.conn is not None
