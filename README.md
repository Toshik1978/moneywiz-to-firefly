# MoneyWiz → Firefly III migration

A command-line tool that migrates your full [MoneyWiz](https://www.wiz.money/) transaction
history into [Firefly III](https://www.firefly-iii.org/) using a MoneyWiz CSV export.

It parses accounts, currencies, payees, categories, tags, payments and transfers, links the
two sides of each transfer back together, stores everything in a local SQLite "staging"
database, and then pushes it to a Firefly III instance through the REST API.

> ⚠️ Investment / brokerage and crypto accounts are **not** properly supported. MoneyWiz
> exports those in a way that doesn't map cleanly onto Firefly III's model. Expect to handle
> them manually.

## How it works

The migration runs in **two phases** that share a local SQLite database (the "staging DB").

```
MoneyWiz CSV ──(import)──▶ SQLite staging DB ──(export)──▶ Firefly III (REST API)
```

1. **Import** (default mode) — parse the CSV, link transfer pairs, deduplicate, and write
   normalized records into the staging DB. Nothing touches Firefly III yet.
2. **Export** (`--export`) — read the staging DB and create the matching currencies,
   accounts, categories, tags, payees and transactions in Firefly III. The Firefly ID of
   every created object is written back to the staging DB.

Because Firefly IDs are stored back into the staging DB, **export is idempotent**: re-running
it only sends records that haven't been exported yet (those with no `firefly_id`). Combined
with `--dedup` on import, you can run the migration incrementally as you add more MoneyWiz
data.

## Requirements

- Python ≥ 3.14
- [uv](https://docs.astral.sh/uv/) (recommended)
- A running Firefly III instance and a Personal Access Token

## Exporting from MoneyWiz

To get a usable CSV:

1. **Unarchive every account** you have ever had (including closed ones).
2. Run a **full CSV export** covering the **entire date range**.

The exporter expects MoneyWiz's CSV columns: `Account`, `Name`, `Current balance`,
`Transfers`, `Payee`, `Category`, `Description`, `Amount`, `Balance`, `Currency`, `Date`,
`Time`, `Tags`. Dates are parsed as `dd/mm/yyyy` and times as `HH:MM`.

## Usage

The tool is exposed as the `moneywiz-to-firefly` console script. With `uv` you can run it
straight from a checkout — `uv run` builds/installs the project into a managed environment
automatically:

```bash
uv run moneywiz-to-firefly --help
```

### 1. Import a CSV into the staging DB

```bash
uv run moneywiz-to-firefly --dbpath .db report.csv
```

Add `--dedup` to skip records that already exist in the staging DB (useful when importing
overlapping exports):

```bash
uv run moneywiz-to-firefly --dbpath .db --dedup report.csv
```

### 2. Export the staging DB to Firefly III

```bash
uv run moneywiz-to-firefly --dbpath .db --export \
  --url https://firefly.example.com \
  --token "$FIREFLY_TOKEN" \
  --config config.json
```

### Configuration

Firefly URL and token can be provided as flags, environment variables (`FIREFLY_URL`,
`FIREFLY_TOKEN`), or via a `.env` file (see [`.env.dist`](.env.dist)).

| Flag        | Env var         | Description                                         |
| ----------- | --------------- | --------------------------------------------------- |
| `--url`     | `FIREFLY_URL`   | Firefly III base URL (export mode)                  |
| `--token`   | `FIREFLY_TOKEN` | Firefly III Personal Access Token (export mode)     |
| `--dbpath`  | —               | Directory holding the SQLite staging DB (`.db`)     |
| `--config`  | —               | JSON file describing account types/roles (export)   |
| `--dedup`   | —               | Deduplicate against the staging DB (import)         |
| `--export`  | —               | Export mode (omit for import mode)                  |
| `-v`        | —               | Verbose logging                                     |

The `--config` JSON file maps MoneyWiz account names to Firefly III account types and roles
(asset / liability / credit card, opening balances, loan interest categories, accounts to
ignore, etc.). MoneyWiz CSV exports don't carry this information, so it must be supplied here.
See [`firefly/config.py`](firefly/config.py) for the full schema.

### Helper script

[`update_firefly.sh`](update_firefly.sh) is a personal convenience wrapper that ships a CSV to
a remote server over SSH and runs import + export there. It contains hard-coded host/path
values and is **not** meant for general use — treat it as an example.

## Known limitations & gotchas

- **Transfers come as two CSV rows** (one per side) that must be matched back together. The
  linker matches on account pair + date + time first, then falls back to same-day and
  same-month matching. If the two sides have mismatched timestamps you may need to align the
  times in MoneyWiz so they pair correctly — otherwise the import fails with "orphaned
  transfers".
- **Investment / brokerage / crypto accounts** don't map cleanly and aren't supported.
- There are currently **no automated tests**.

## License

See [LICENSE](LICENSE).
