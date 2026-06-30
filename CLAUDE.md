# CLAUDE.md

Guidance for working in this repository.

## What this project is

A CLI tool that migrates a full MoneyWiz transaction history into Firefly III from a MoneyWiz
CSV export. It runs in two phases sharing a local SQLite "staging" database:

1. **Import** (default): parse CSV → link transfer pairs → optionally dedup → write to SQLite.
2. **Export** (`--export`): read SQLite → create objects in Firefly III via REST → write the
   returned `firefly_id` back to SQLite (makes export idempotent).

## Commands

This is an installable project (hatchling build backend) exposing the `moneywiz-to-firefly`
console script. `uv run` builds/installs it into a managed env automatically. Dependencies
live in **one place**: `pyproject.toml`.

```bash
# Import a CSV into the staging DB (.db dir)
uv run moneywiz-to-firefly --dbpath .db [--dedup] report.csv

# Export the staging DB to Firefly III
uv run moneywiz-to-firefly --dbpath .db --export --url <URL> --token <TOKEN> --config config.json

# Verbose logging
uv run moneywiz-to-firefly -v ...
```

`FIREFLY_URL` / `FIREFLY_TOKEN` can come from env vars or a `.env` file (Click
`auto_envvar_prefix='FIREFLY'`).

### Quality checks

```bash
uv run ruff check .          # lint
uv run ruff format .         # format (config: line-length 120, rules E/F/I/UP/B)
uv run pytest                # tests (tests/, pure logic: helpers, transfer linker, importer)
```

CI (`.github/workflows/ci.yml`) runs `ruff check`, `ruff format --check`, and `pytest` on
push to `main` and on PRs.

Note: `tests/test_analyzer_fresh_db.py` has a **strict xfail** documenting a known bug — a
first import into an empty DB fails because a new currency has no `id` yet when accounts are
validated. If you fix that, the xfail will start failing (strict) and the marker should be
removed.

## Architecture

The entry point is `cli.py` (`cli:main`, a Click CLI). Three packages, each a layer:

- **`moneywiz/`** — read side. `importer.py` parses CSV rows into `Mw*` dataclasses
  (`scheme.py`). A row is an **account** if it has a `Name`, a **transfer** if it has
  `Transfers`, otherwise a **payment**. Per-entity analyzers (`account.py`, `payment.py`,
  `transfer.py`, …) convert `Mw*` dataclasses into `storage/` ORM objects, deduplicating
  against what's already in the DB. `analyzer.py` orchestrates them in dependency order.
- **`storage/`** — SQLite via SQLAlchemy. `scheme.py` has the ORM models
  (`Currency`, `Payee`, `Category`, `Tag`, `Account`, `Transfer`, `Payment`);
  `transactions.py` (`TransactionsDB`) is the data-access layer. `firefly_id` columns track
  what has been exported; `get_transfers`/`get_payments` return only rows where
  `firefly_id IS NULL`.
- **`firefly/`** — write side. One exporter per entity type, orchestrated by `exporter.py` in
  dependency order (currencies → categories → tags → payees → accounts → payments →
  transfers). `client.py` wraps the `firefly-iii-client` SDK. `config.py` parses the
  `--config` JSON that supplies account types/roles MoneyWiz doesn't export.

`helpers.py` holds shared utilities: `to_datetime` (dd/mm/yyyy + HH:MM), `to_amount` (strips
`-+,`), `hash_key` (join with `-`), `filter_utf8` (normalize MoneyWiz CSV glyphs).

## Domain concepts that bite

- **Transfer linking is the hard part.** MoneyWiz exports each transfer as **two rows** (the
  debit side and the credit side). `moneywiz/transfer.py` matches them into one `Transfer`
  using progressively looser keys: exact (source+target+date+time+category) → same date →
  same month. Unmatched rows raise `AnalyzerException("Orphaned transfers...")`. The sign of
  the amount decides which row is source vs target.
- **Sign convention:** an amount starting with `-` is a withdrawal / the source side.
- **Payment splits:** `firefly/payment.py` groups payments by account + payee + type + minute
  and creates a Firefly split transaction when more than one falls in the same bucket.
- **Liability transfers** (loan payments) are special-cased into withdrawals in
  `firefly/transfer.py`, using `loan_payment_category` / `loan_interest_category` from config.
- **Idempotency:** never assume export is fresh. It only sends un-exported rows. Re-running is
  safe by design — preserve that property.

## Conventions

- Python ≥ 3.14. Modern typing (`str | None`, `Self`, builtin generics).
- Heavy use of "private" name-mangled attributes (`self.__x`) and class-level type
  annotations documenting structure.
- Analyzers/exporters share a shape: constructor takes deps, `analyze()`/`sync()` does the
  work and returns `Self`, `get()` returns results.
- Flat layout: top-level modules (`cli.py`, `helpers.py`) plus the three packages, all listed
  in `[tool.hatch.build.targets.wheel].only-include`. Add new top-level modules/packages there
  or they won't ship in the wheel. Imports are absolute (`from firefly...`, `from helpers...`).

## Git conventions

- **Never add `Co-Authored-By` trailers** (or any AI attribution) to commit messages.

## Gotchas when editing

- New top-level modules/packages must be added to `only-include` in `pyproject.toml`.
- `update_firefly.sh` contains hard-coded SSH host/paths — it's a personal helper, not generic.
- Investment / brokerage / crypto accounts are known-unsupported; don't assume they work.
