# Quickstart (10 minutes)

This guide gets you from installing Shoveler to your first query quickly.

## 1) Install and run

### Windows and Linux: download the desktop app

1. Open the [latest GitHub Release](https://github.com/mrmatho/shoveler/releases/latest).
2. Download the Windows or Linux desktop package.
3. Extract the package and launch Shoveler.

This is the recommended option for students, teachers, and most users. It does
not require installing Python or other development tools.

### macOS: install with pip

The macOS desktop build is not signed or notarized, so install with pip instead:

```shell
pip install shoveler
python -m shoveler
```

Building from source is intended for developers. See the
[developer guide](../DEVELOPMENT.md).

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

![A completed query in Shoveler with the students table and sorted results](images/workbench-light.png)

*The schema panel shows the new table, and the results panel shows students sorted by grade.*

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

Click a column header to sort the results table (an arrow ▲/▼ shows the direction). Click again for descending, and a third time to return to the original order, and type in the **Filter results...** box to show only rows containing that text. Sorting and filtering only change what you see; export always uses the original query results in their original order ("Selected" exports the rows you highlighted).

## 8) Export your SQL

Use the **Export SQL** button in the query tab toolbar to save your editor content as a `.sql` file.

## 9) Adjust text size

Use **View > Zoom** to increase, decrease, or reset font size for:

- the SQL editor
- the results table/status area

Keyboard shortcuts:

- Editor: `Ctrl+=`, `Ctrl+-`, `Ctrl+0`
- Results: `Ctrl+Shift+=`, `Ctrl+Shift+-`, `Ctrl+Shift+0`

## Next

- Read [Core Concepts](concepts.md)
- Keep [Troubleshooting](troubleshooting.md) open during labs
