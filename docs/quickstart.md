# Quickstart (10 minutes)

This guide gets you from clone to first query quickly.

## 1) Install and run

Using UV:

```shell
uv pip install shoveler
uv run python -m shoveler
```

Using pip:

```shell
pip install shoveler
python -m shoveler
```

## 2) Choose a database mode

When the app opens, choose one:

- Open DB File: Use an existing `.duckdb` or `.db` file.
- New Blank DB: Start an in-memory database for experiments.

*Tip: In-memory databases are temporary until you save them.*

## 3) Run your first SQL

Paste this into the SQL editor:

```sql
create table students (
  id integer,
  name varchar,
  grade integer
);

insert into students values
  (1, 'Ahmed', 88),
  (2, 'Belinda', 92),
  (3, 'Cleo', 79);

select * from students order by grade desc;
```

Run it with:

- `F5`, or
- `Ctrl+Enter`, or
- the Run Query button

## 4) Try selection-only execution

1. Highlight only the final `select` statement.
2. Run query again.
3. Confirm only the selected SQL is executed.

## 5) Explore schema and insert table names

1. Look at the schema panel for `students`.
2. Double-click `students` to insert its name into the editor.

## 6) Save your work (if in-memory)

Use File > Save Database As... to persist an in-memory database to disk.

## 7) Export results

Run a query, then use the results export menu to save CSV output.

## Next

- Read [Core Concepts](concepts.md)
- Keep [Troubleshooting](troubleshooting.md) open during labs
