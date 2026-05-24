"""
Tests for the Database layer.
No display required — db.py has no PySide6 imports.
"""

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
    assert len(result["rows"]) == 2
    assert result["rows"][0] == (1, "Alice", 85)


def test_invalid_sql_returns_error(db):
    result = db.execute("SELECT * FROM nonexistent_table")
    assert result["error"] is not None
    assert result["columns"] == []
    assert result["rows"] == []


def test_ddl_returns_count_column(db):
    # DuckDB returns a single 'Count' column for DDL statements
    result = db.execute("CREATE TABLE t (x INTEGER)")
    assert result["error"] is None
    assert result["columns"] == ["Count"]


def test_elapsed_is_positive(db_with_table):
    result = db_with_table.execute("SELECT * FROM students")
    assert result["elapsed"] > 0


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


def test_get_tables_no_connection():
    db = Database()
    assert db.get_tables() == []


def test_get_columns_no_connection():
    db = Database()
    assert db.get_columns("anything") == []


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
