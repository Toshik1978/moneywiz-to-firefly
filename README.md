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

The exporter expects MoneyWiz's CSV columns: `Name`, `Current balance`, `Account`,
`Transfers`, `Description`, `Payee`, `Category`, `Date`, `Time`, `Amount`, `Currency`,
`Check #`, `Tags`, `Balance`. Dates are parsed as `dd/mm/yyyy` and times as `HH:MM`. On an
account-definition row the currency code lives in the `Account` column and the account name
in `Name`.

MoneyWiz prepends a `sep=,` hint line (and a UTF-8 BOM) to raw exports. The importer detects
and skips that line automatically, so **both raw exports and files that already had it
stripped import fine** — no preprocessing required.

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

[`update_firefly.sh`](update_firefly.sh) is a convenience wrapper that ships a CSV to a remote
host over SSH and runs import + export there. Configure it via environment variables or a
`.env` file beside the script (see [`.env.dist`](.env.dist)):

| Variable             | Description                                                       |
| -------------------- | ----------------------------------------------------------------- |
| `DEPLOY_SSH_HOST`    | SSH host: `user@host` or a `~/.ssh/config` alias                  |
| `DEPLOY_REMOTE_PATH` | Base dir on the host holding `reports/`, `db/`, and `config.json` |
| `DEPLOY_PROJECT_DIR` | Path to the `moneywiz-to-firefly` checkout on the host            |
| `DEPLOY_PATH_PREFIX` | Optional: dir to prepend to the host's `PATH` so `uv` is found (mise shims; empty = leave PATH as-is) |

Paths that should expand on the **host** (e.g. using `$HOME`) must be single-quoted in `.env`
so they aren't expanded locally — e.g. `DEPLOY_PROJECT_DIR='$HOME/moneywiz-to-firefly'`. The
host also needs its own Firefly credentials (`FIREFLY_URL` / `FIREFLY_TOKEN`) for the export
step.

## Known limitations & gotchas

- **Transfers come as two CSV rows** (one per side) that must be matched back together. The
  linker matches on account pair + date + time first, then falls back to same-day and
  same-month matching. Two failure modes need manual fixes in the source data:
  - *Mismatched timestamps* — if the two sides of a transfer have different times (and fall
    in different months), they won't pair. Align the times so they match.
  - *Timestamp collisions* — if **two different transfers** between the **same pair of
    accounts** happen at the **exact same date and time**, the linker can't tell their sides
    apart and one stays unpaired. Nudge one transfer's time by a minute (on **both** of its
    rows) to disambiguate.

  Both surface as an `AnalyzerException` (`orphaned transfers` or `missing transfers detected:
  N vs M`, where `N - M` is the number of unpaired rows).
- **Investment / brokerage / crypto accounts** don't map cleanly and aren't supported.

## License

See [LICENSE](LICENSE).
