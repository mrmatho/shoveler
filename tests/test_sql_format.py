import pytest

from shoveler.sql_format import find_delimiter_error, format_sql, split_statement_spans


def test_keywords_uppercased_and_clauses_indented():
    out = format_sql("select a, b from t where a > 1 and b < 2 order by a")
    assert out == "SELECT a, b\nFROM t\nWHERE a > 1\n    AND b < 2\nORDER BY a"


def test_statements_separated_by_blank_line():
    out = format_sql("select 1; select 2;")
    assert out == "SELECT 1;\n\nSELECT 2;"


def test_strings_and_identifiers_untouched():
    out = format_sql("select 'from; where', \"select\" from t")
    assert "'from; where'" in out and '"select"' in out


@pytest.mark.parametrize(
    "literal",
    [
        "$$hello$$",
        "$$a;b ([)] -- /* ' \"\nwhere$$",
        "$tag$a; $other$ ( ] $TAG$ b$tag$",
        "$_tag1$from, select$_tag1$",
        "$💡$a;b$💡$",
        "$$$$",
    ],
)
def test_dollar_quoted_literals_are_preserved(literal):
    sql = f"select {literal}; select 2;"
    assert format_sql(sql) == f"SELECT {literal};\n\nSELECT 2;"
    assert [sql[start:end] for start, end in split_statement_spans(sql)] == [
        f"select {literal}",
        "select 2",
    ]
    assert find_delimiter_error(sql) is None


@pytest.mark.parametrize("literal", ["$$unclosed; (", "$tag$unclosed; ] $TAG$"])
def test_unclosed_dollar_quoted_literal(literal):
    sql = f"SELECT {literal}"
    assert split_statement_spans(sql) == [(0, len(sql))]
    assert find_delimiter_error(sql) == (7, f"Unclosed string: missing closing {literal[:literal.index('$', 1) + 1]}")
    assert format_sql(sql) == sql


def test_dollars_in_identifiers_and_parameters_are_not_dollar_quotes():
    sql = "select column$$name, $value from t;"
    assert format_sql(sql) == "SELECT column$$name, $ value\nFROM t;"
    assert find_delimiter_error(sql) is None


def test_between_and_not_split():
    assert "BETWEEN 1 AND 2" in format_sql("select * from t where a between 1 and 2")


def test_empty():
    assert format_sql("  ") == ""


def test_short_column_list_stays_inline():
    assert format_sql("select a, b, c from t") == "SELECT a, b, c\nFROM t"


def test_long_column_list_one_per_line():
    out = format_sql("select a, b, c, d from t")
    assert out == "SELECT\n    a,\n    b,\n    c,\n    d\nFROM t"


def test_function_names_uppercased():
    out = format_sql("select count(*), sum(x) from t")
    assert out == "SELECT COUNT(*), SUM(x)\nFROM t"


def test_nested_commas_do_not_count():
    assert format_sql("select coalesce(a, b, c, d) from t") == "SELECT COALESCE(a, b, c, d)\nFROM t"
