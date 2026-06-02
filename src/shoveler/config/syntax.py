from .theme import normalize_theme


SQL_KEYWORDS = (
    "SELECT",
    "FROM",
    "WHERE",
    "GROUP",
    "BY",
    "ORDER",
    "HAVING",
    "LIMIT",
    "JOIN",
    "DISTINCT",
    "INSERT",
    "INTO",
    "VALUES",
    "UPDATE",
    "SET",
    "DELETE",
    "CREATE",
    "ALTER",
    "DROP",
    "TABLE",
    "VIEW",
    "INDEX",
    "REPLACE",
    "OR",
    "AND",
    "NOT",
    "PRIMARY",
    "KEY",
    "FOREIGN",
    "LEFT",
    "RIGHT",
    "FULL",
    "OUTER",
    "CROSS",
    "ON",
    "AS",
    "WITH",
    "UNION",
    "ALL",
    "NULL",
    "IS",
    "LIKE",
    "IN",
    "BETWEEN",
    "CASE",
    "WHEN",
    "THEN",
    "ELSE",
    "END",
    "EXISTS",
    "REFERENCES",
    "DEFAULT",
    "CHECK",
    "INNER",
    "OFFSET",

)

SQL_TYPE_NAMES = (
    "INTEGER",
    "BIGINT",
    "SMALLINT",
    "DOUBLE",
    "DECIMAL",
    "NUMERIC",
    "REAL",
    "BOOLEAN",
    "VARCHAR",
    "TEXT",
    "TIMESTAMP",
    "DATE",
    "TIME",
    "BLOB",
)

SQL_FUNCTIONS = (
    "COUNT",
    "SUM",
    "AVG",
    "MIN",
    "MAX",
    "COALESCE",
    "ROUND",
    "CAST",
    "NOW",
    "DATE_TRUNC",
    "CURRENT_DATE",
    "CURRENT_TIMESTAMP",
)

_SYNTAX_PALETTES = {
    "light": {
        "keyword": "#005cc5",
        "type": "#6f42c1",
        "function": "#d73a49",
        "string": "#22863a",
        "number": "#b08800",
        "comment": "#6a737d",
        "identifier": "#032f62",
    },
    "dark": {
        "keyword": "#66b7ff",
        "type": "#c39aff",
        "function": "#ff8b93",
        "string": "#edb211",
        "number": "#e4b763",
        "comment": "#92a2b7",
        "identifier": "#88c8ff",
    },
    "vivid": {
        "keyword": "#70e6ff",
        "type": "#ff9ff3",
        "function": "#ff857a",
        "string": "#7dff98",
        "number": "#ffd86b",
        "comment": "#9cc0ff",
        "identifier": "#b693ff",
    },
}

_LINE_NUMBER_PALETTES = {
    "light": {
        "background": "#edf3fb",
        "foreground": "#70839a",
        "border": "#d7deea",
    },
    "dark": {
        "background": "#242f40",
        "foreground": "#8fa1b7",
        "border": "#3b4659",
    },
    "vivid": {
        "background": "#2c2152",
        "foreground": "#c4d4ff",
        "border": "#5d54a8",
    },
}


def get_syntax_palette(theme: str) -> dict[str, str]:
    return _SYNTAX_PALETTES[normalize_theme(theme)]


def get_line_number_palette(theme: str) -> dict[str, str]:
    return _LINE_NUMBER_PALETTES[normalize_theme(theme)]
