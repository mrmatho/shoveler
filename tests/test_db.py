"""
Tests for the Database layer.
No display required — db.py has no PySide6 imports.
"""

import logging

import pytest
from shoveler.db import Database


@pytest.fixture
def db():
    database = Database()
    database.new_memory()
    yield database
    database.close()


@pytest.fixture
def db_with_table(db):
    db.execute("CREATE TABLE students (id INTEGER, name VARCHAR, grade INTEGER)")
    db.execute("INSERT INTO students VALUES (1, 'Alice', 85), (2, 'Bob', 72)")
    return db


# ── Connection state ────────────────────────────────────────────────────────

def test_new_memory_sets_mode(db):
    assert db.mode == "memory"
    assert db.path is None
    assert db.is_connected


def test_open_file_sets_mode(tmp_path):
    path = str(tmp_path / "test.duckdb")
    db = Database()
    db.open_file(path)
    assert db.mode == "file"
    assert db.path == path
    assert db.is_connected
    db.close()


def test_close_clears_state(db):
    db.close()
    assert not db.is_connected
    assert db.mode is None


def test_no_connection_returns_error():
    db = Database()
    result = db.execute("SELECT 1")
    assert result["error"] is not None


# ── Query execution ─────────────────────────────────────────────────────────

def test_select_returns_columns_and_rows(db_with_table):
    result = db_with_table.execute("SELECT * FROM students ORDER BY id")
    assert result["error"] is None
    assert result["columns"] == ["id", "name", "grade"]
    assert result["column_types"] == ["INTEGER", "VARCHAR", "INTEGER"]
    assert len(result["rows"]) == 2
    assert result["rows"][0] == (1, "Alice", 85)


def test_invalid_sql_returns_error(db):
    result = db.execute("SELECT * FROM nonexistent_table")
    assert result["error"] is not None
    assert result["columns"] == []
    assert result["column_types"] == []
    assert result["rows"] == []


def test_ddl_returns_count_column(db):
    # DuckDB returns a single 'Count' column for DDL statements
    result = db.execute("CREATE TABLE t (x INTEGER)")
    assert result["error"] is None
    assert result["columns"] == ["Count"]
    assert result["column_types"] == ["BIGINT"]


def test_elapsed_is_positive(db_with_table):
    result = db_with_table.execute("SELECT * FROM students")
    assert result["elapsed"] > 0


def test_execute_returns_full_result_key_set(db_with_table):
    result = db_with_table.execute("SELECT * FROM students ORDER BY id")

    assert set(result.keys()) == {"columns", "column_types", "rows", "elapsed", "error"}


# ── Schema introspection ────────────────────────────────────────────────────

def test_get_tables(db_with_table):
    tables = db_with_table.get_tables()
    assert "students" in tables


def test_get_tables_empty(db):
    assert db.get_tables() == []


def test_get_columns(db_with_table):
    cols = db_with_table.get_columns("students")
    names = [name for name, _ in cols]
    assert names == ["id", "name", "grade"]


def test_get_columns_includes_types(db_with_table):
    cols = db_with_table.get_columns("students")
    type_map = dict(cols)
    assert "INTEGER" in type_map["id"]
    assert "VARCHAR" in type_map["name"]


def test_get_columns_supports_table_names_requiring_identifier_quotes(db):
    db.execute('CREATE TABLE "order details" ("student id" INTEGER, note VARCHAR)')

    cols = db.get_columns("order details")

    assert cols == [("student id", "INTEGER"), ("note", "VARCHAR")]


def test_get_column_key_flags_primary_key(db):
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name VARCHAR)")

    flags = db.get_column_key_flags("users")

    assert flags["id"] == (True, False)
    assert flags["name"] == (False, False)


def test_get_column_key_flags_foreign_key(db):
    db.execute("CREATE TABLE parents (id INTEGER PRIMARY KEY)")
    db.execute(
        "CREATE TABLE children (id INTEGER, parent_id INTEGER, "
        "FOREIGN KEY(parent_id) REFERENCES parents(id))"
    )

    flags = db.get_column_key_flags("children")

    assert flags["id"] == (False, False)
    assert flags["parent_id"] == (False, True)


def test_get_column_key_info_foreign_key_includes_referenced_table(db):
    db.execute("CREATE TABLE parents (id INTEGER PRIMARY KEY)")
    db.execute(
        "CREATE TABLE children (id INTEGER, parent_id INTEGER, "
        "FOREIGN KEY(parent_id) REFERENCES parents(id))"
    )

    info = db.get_column_key_info("children")

    assert info["id"] == {"is_primary_key": False, "referenced_table": None}
    assert info["parent_id"] == {
        "is_primary_key": False,
        "referenced_table": "parents",
    }


def test_get_tables_no_connection():
    db = Database()
    assert db.get_tables() == []


def test_get_columns_no_connection():
    db = Database()
    assert db.get_columns("anything") == []


def test_get_columns_logs_failure_for_invalid_table_name(db, caplog):
    with caplog.at_level(logging.ERROR, logger="shoveler.db"):
        cols = db.get_columns("missing table")

    assert cols == []
    assert "Failed to describe table 'missing table'" in caplog.text


# ── File checkpoint ─────────────────────────────────────────────────────────

def test_checkpoint_file_db(tmp_path):
    path = str(tmp_path / "test.duckdb")
    db = Database()
    db.open_file(path)
    db.execute("CREATE TABLE t (x INTEGER)")
    db.checkpoint()  # should not raise
    db.close()


def test_checkpoint_memory_db_is_noop(db):
    db.checkpoint()  # should not raise


# ── Save as file ───────────────────────────────────────────────────────────

def test_save_as_memory_db_writes_file_and_switches_mode(tmp_path):
    db = Database()
    db.new_memory()
    db.execute("CREATE TABLE t (x INTEGER)")
    db.execute("INSERT INTO t VALUES (1), (2)")

    path = str(tmp_path / "saved.duckdb")
    saved_path = db.save_as(path)

    assert saved_path == path
    assert db.mode == "file"
    assert db.path == path
    assert (tmp_path / "saved.duckdb").exists()

    result = db.execute("SELECT COUNT(*) AS n FROM t")
    assert result["error"] is None
    assert result["rows"][0][0] == 2
    db.close()


def test_save_as_same_file_path_is_checkpoint(tmp_path):
    path = str(tmp_path / "existing.duckdb")
    db = Database()
    db.open_file(path)
    db.execute("CREATE TABLE t (x INTEGER)")

    saved_path = db.save_as(path)

    assert saved_path == path
    assert db.mode == "file"
    assert db.path == path
    db.close()


def test_save_as_no_connection_raises():
    db = Database()
    with pytest.raises(RuntimeError, match="No database connected"):
        db.save_as("any.duckdb")
