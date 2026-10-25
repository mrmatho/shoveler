from shoveler.sql_format import format_sql


def test_keywords_uppercased_and_clauses_indented():
    out = format_sql("select a, b from t where a > 1 and b < 2 order by a")
    assert out == "SELECT a,\n    b\nFROM t\nWHERE a > 1\n    AND b < 2\nORDER BY a"


def test_statements_separated_by_blank_line():
    out = format_sql("select 1; select 2;")
    assert out == "SELECT 1;\n\nSELECT 2;"


def test_strings_and_identifiers_untouched():
    out = format_sql("select 'from; where', \"select\" from t")
    assert "'from; where'" in out and '"select"' in out


def test_between_and_not_split():
    assert "BETWEEN 1 AND 2" in format_sql("select * from t where a between 1 and 2")


def test_empty():
    assert format_sql("  ") == ""
