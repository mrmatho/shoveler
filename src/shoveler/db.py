import duckdb
import os
import time
from typing import Literal


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

    def execute(self, sql: str) -> dict:
        """Returns dict: columns, rows, elapsed, error"""
        if not self.conn:
            return {
                "columns": [],
                "rows": [],
                "elapsed": 0.0,
                "error": "No database connected.",
            }
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
            return {"columns": columns, "rows": rows, "elapsed": elapsed, "error": None}
        except Exception as e:
            elapsed = time.perf_counter() - start
            return {"columns": [], "rows": [], "elapsed": elapsed, "error": str(e)}

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
