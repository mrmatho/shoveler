"""Lightweight SQL formatter: indentation, upper-case keywords, one statement per block."""

import re

INDENT = "    "

_TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
    |(?P<comment>--[^\n]*|/\*.*?(?:\*/|\Z))
    |(?P<string>'(?:[^']|'')*(?:'|\Z))
    |(?P<quoted>"(?:[^"]|"")*(?:"|\Z))
    |(?P<word>[A-Za-z_][A-Za-z0-9_$]*)
    |(?P<number>\d+(?:\.\d+)?)
    |(?P<op><>|!=|<=|>=|\|\||::|[-+*/%=<>])
    |(?P<punct>[(),;.\[\]])
    |(?P<other>.)
    """,
    re.VERBOSE | re.DOTALL,
)

KEYWORDS = frozenset(
    """
    ADD ALL ALTER AND ANY AS ASC BETWEEN BY CASE CAST CREATE CROSS CURRENT_DATE
    CURRENT_TIMESTAMP DEFAULT DELETE DESC DISTINCT DROP ELSE END EXCEPT EXISTS FALSE
    FETCH FIRST FOLLOWING FROM FULL GROUP HAVING ILIKE IN INNER INSERT INTERSECT
    INTERVAL INTO IS JOIN LEFT LIKE LIMIT NATURAL NOT NULL NULLS OFFSET ON OR ORDER
    OUTER OVER PARTITION PRECEDING PRIMARY QUALIFY RANGE RECURSIVE REPLACE RIGHT ROW
    ROWS SELECT SET TABLE THEN TRUE UNBOUNDED UNION UNIQUE UPDATE USING VALUES VIEW
    WHEN WHERE WINDOW WITH
    """.split()
)

# Clause starters that begin a new line at the statement's base indent.
_CLAUSES = ("SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "HAVING", "LIMIT",
            "OFFSET", "QUALIFY", "WINDOW", "VALUES", "SET", "UNION", "UNION ALL",
            "INTERSECT", "EXCEPT", "INSERT INTO", "UPDATE", "DELETE FROM", "WITH")
_JOIN_PREFIXES = {"LEFT", "RIGHT", "FULL", "INNER", "CROSS", "NATURAL", "OUTER"}


def _tokenize(sql: str) -> list[tuple[str, str]]:
    return [
        (m.lastgroup, m.group())
        for m in _TOKEN_RE.finditer(sql)
        if m.lastgroup != "ws"
    ]


def _split_statements(tokens: list[tuple[str, str]]) -> list[list[tuple[str, str]]]:
    statements: list[list[tuple[str, str]]] = []
    current: list[tuple[str, str]] = []
    for kind, text in tokens:
        current.append((kind, text))
        if kind == "punct" and text == ";":
            statements.append(current)
            current = []
    if current:
        statements.append(current)
    return statements


def _format_statement(tokens: list[tuple[str, str]]) -> str:
    lines: list[str] = []
    line = ""
    depth = 0
    in_list = False  # inside a top-level comma-separated list
    in_condition = False  # inside WHERE / HAVING / ON
    pending_between = False
    prev_kind, prev_text = "", ""

    def flush(indent: str = ""):
        nonlocal line
        if line.strip():
            lines.append(line.rstrip())
        line = indent

    upper_words = [t.upper() if k == "word" else "" for k, t in tokens]
    for i, (kind, text) in enumerate(tokens):
        if kind == "word" and text.upper() in KEYWORDS:
            text = text.upper()
        word = text if kind == "word" else ""
        nxt = upper_words[i + 1] if i + 1 < len(tokens) else ""

        if kind == "comment":
            if line.strip():
                line += " "
            line += text
            if text.startswith("--"):
                flush(INDENT if in_list and depth == 0 else "")
            prev_kind, prev_text = kind, text
            continue

        if depth == 0 and kind == "word":
            up = word.upper()
            # Resolve multi-word clause starters on first word only.
            is_clause = (
                (up in ("GROUP", "ORDER") and nxt == "BY")
                or (up == "UNION")
                or (up in ("INTERSECT", "EXCEPT"))
                or (up in ("SELECT", "FROM", "WHERE", "HAVING", "LIMIT", "OFFSET",
                           "QUALIFY", "WINDOW", "VALUES", "SET", "WITH", "UPDATE"))
                or (up == "INSERT" and nxt == "INTO")
                or (up == "DELETE" and nxt == "FROM")
            )
            is_join = up == "JOIN" and prev_text.upper() not in _JOIN_PREFIXES
            is_join = is_join or (
                up in _JOIN_PREFIXES
                and prev_text.upper() not in _JOIN_PREFIXES
                and any(w == "JOIN" for w in upper_words[i + 1 : i + 4])
            )
            # DELETE FROM / INSERT INTO: do not break at the second keyword.
            if up == "FROM" and prev_text.upper() == "DELETE":
                is_clause = False
            if up in ("SELECT",) and prev_text.upper() in ("UNION", "ALL", "INTERSECT", "EXCEPT"):
                is_clause = True
            if is_clause or is_join:
                if line.strip():
                    flush()
                in_list = up in ("SELECT", "GROUP", "ORDER", "SET", "WITH")
                in_condition = up in ("WHERE", "HAVING", "QUALIFY")
                pending_between = False
                line = ""
                if is_join:
                    in_list = False
                line += text
                prev_kind, prev_text = kind, text
                continue
            if up == "BETWEEN":
                pending_between = True
            elif up == "AND" and pending_between:
                pending_between = False
            elif up in ("AND", "OR") and in_condition:
                flush(INDENT)
                line += text
                prev_kind, prev_text = kind, text
                continue

        if kind == "punct" and text == ";":
            line = line.rstrip() + ";"
            prev_kind, prev_text = kind, text
            continue
        if kind == "punct" and text == ",":
            line = line.rstrip() + ","
            if depth == 0 and in_list:
                flush(INDENT)
            prev_kind, prev_text = kind, text
            continue

        if kind == "punct" and text == "(":
            if prev_kind == "word" and prev_text.upper() not in KEYWORDS - {"REPLACE"}:
                pass  # function call: no space
            elif line.strip():
                line = line.rstrip() + " "
            line += "("
            depth += 1
            prev_kind, prev_text = kind, text
            continue
        if kind == "punct" and text == ")":
            depth = max(0, depth - 1)
            line = line.rstrip() + ")"
            prev_kind, prev_text = kind, text
            continue

        no_space_before = (kind == "punct" and text in (".", "[", "]")) or (
            prev_kind == "punct" and prev_text in (".", "(", "[")
        ) or (kind == "op" and text == "::") or (prev_kind == "op" and prev_text == "::")
        if line.strip() == "" and not lines:
            line = text
        elif line.strip() == "":
            line = line + text
        elif no_space_before:
            line += text
        else:
            line += " " + text
        prev_kind, prev_text = kind, text

    flush()
    # First line of a list-style clause: indent following content is handled by commas;
    # keep the first item on the clause line for compactness.
    return "\n".join(lines)


def format_sql(sql: str) -> str:
    """Return sql with upper-case keywords, indentation, and blank lines between statements."""
    tokens = _tokenize(sql)
    statements = [_format_statement(s) for s in _split_statements(tokens)]
    return "\n\n".join(s for s in statements if s.strip())
