# Troubleshooting

Common setup and runtime issues for classroom and self-study use.

## App does not start after clone

1. Run `uv sync` in the project root.
2. Run `uv run python -m shoveler`.
3. If still failing, ensure your Python and `uv` installation are available in your shell.

## Import or package metadata errors

If you see `PackageNotFoundError` or missing package errors:

1. Re-run `uv sync`.
2. Verify package metadata with:

```shell
python -c "import importlib.metadata as m; print(m.version('shoveler'))"
```

## Query runs but no data appears

1. Check the results panel for error messages.
2. Confirm you are querying the expected table and database mode.
3. If using in-memory mode, verify you did not restart without saving.

## Checkpoint button is disabled

This is expected in in-memory mode.

Checkpoint is only available for file-backed databases.

## Working directory looks wrong on startup

Shoveler restores the last working directory if it still exists.

If it does not exist, Shoveler uses Home/Documents (if present), otherwise home.

Use Change... in the working directory section to set a new directory.

## Open DB file fails

1. Confirm the file path exists and you have read/write access.
2. Try opening the file outside synced cloud folders if file locking is suspected.
3. Retry with a new test database to isolate whether the file is corrupted.

## Tests fail locally

Run:

```shell
uv run pytest
```

If failures continue after syncing dependencies, capture the traceback and include it in an issue.

## Need help

Open a GitHub issue with:

- your OS
- the command you ran
- full error text
- steps to reproduce
