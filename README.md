[![CI](https://github.com/Toshik1978/moneywiz-to-firefly/actions/workflows/ci.yml/badge.svg)](https://github.com/Toshik1978/moneywiz-to-firefly/actions)
![Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Toshik1978/3eaf6c98f6741c091eacd84bad2762c6/raw/tests.json&maxAge=180)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/Toshik1978/3eaf6c98f6741c091eacd84bad2762c6/raw/coverage.json&maxAge=180)

# MoneyWiz → Firefly III migration

A command-line tool that migrates your full [MoneyWiz](https://www.wiz.money/) transaction
history into [Firefly III](https://www.firefly-iii.org/) using a MoneyWiz CSV export.

It parses accounts, currencies, payees, categories, tags, payments and transfers, links the
two sides of each transfer back together, stores everything in a local SQLite "staging"
database, and then pushes it to a Firefly III instance through the REST API.

> ⚠️ Investment / brokerage and crypto accounts are **not** properly supported. MoneyWiz
> exports those in a way that doesn't map cleanly onto Firefly III's model. Expect to handle
> them manually.

## Why I built this

I'd tracked every transaction in MoneyWiz since 2011 — **over a decade of history**:
**25,000+ transactions** across **100+ accounts** in a **handful of currencies**, accumulated
as life moved across countries and banks. Then I switched from iPhone to
Android, and discovered that the otherwise-excellent MoneyWiz team had dropped their Android
app — leaving me with 13 years of finances and no way to keep using them. So I decided to move
to self-hosted Firefly III instead.

Re-entering all of that by hand was obviously off the table, and the importers I tried choked
on the scale, the cross-currency transfers, or MoneyWiz's two-rows-per-transfer export format.
So I wrote this.

The part I'm happiest with: across all of those rows I had to hand-edit only **about three
dozen** — roughly **one line in a thousand**. Nearly all were transfers whose two halves
carried slightly mismatched timestamps (or two transfers between the same accounts in the same
minute); I nudged one side by a minute so the linker could pair them up. A couple were
single-cent corrections. Everything else — every payee, category, split, tag, currency,
opening balance and loan payment — imported and exported untouched.

If your MoneyWiz data looks anything like mine, expect a similarly tiny amount of manual
cleanup.

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

#### The `--config` file

MoneyWiz CSV exports don't carry an account's type, role, opening balance or interest rate, so
the export step reads them from a JSON config you provide. It has two sections: a list of
`accounts` (keyed by the exact MoneyWiz account name) and a block of global `settings`.

> Every account you want in Firefly III must have an entry here. An account that isn't listed
> (or is marked `ignore`) is **not created** — and any payment/transfer referencing it is
> skipped with a warning.

A representative config covering each feature:

```json
{
  "accounts": [
    {
      "name": "Checking - Bank A (€)",
      "active": true
    },
    {
      "name": "Cash (€)",
      "role": "cashWalletAsset",
      "opening_balance_date": "18/08/2011",
      "opening_balance": "500.00",
      "active": true
    },
    {
      "name": "Credit Card - Bank A (€)",
      "role": "ccAsset",
      "payment_date": 14,
      "active": true
    },
    {
      "name": "Savings - Bank A (€)",
      "role": "savingAsset",
      "active": true
    },
    {
      "name": "Mortgage - Bank B (€)",
      "type": "liability",
      "liability_type": "mortgage",
      "interest": "12",
      "opening_balance_date": "16/02/2011",
      "opening_balance": "250000.00",
      "active": true
    },
    {
      "name": "Old Brokerage (€)",
      "role": "savingAsset",
      "active": false
    },
    {
      "name": "Duplicate Wallet (€)",
      "active": false,
      "ignore": true
    }
  ],
  "settings": {
    "default_account_type": "asset",
    "default_account_role": "defaultAsset",
    "loan_payment_category": "Banking - Loan Payment",
    "loan_interest_category": "Banking - Loan Interest"
  }
}
```

**Per-account fields** (only `name` is required; the rest default sensibly):

| Field                  | Applies to     | Description                                                                                          |
| ---------------------- | -------------- | --------------------------------------------------------------------------------------------------- |
| `name`                 | all            | Exact MoneyWiz account name (must match the CSV, currency suffix included).                          |
| `type`                 | all            | `asset` (default) or `liability`.                                                                    |
| `role`                 | asset          | `defaultAsset` (default), `savingAsset`, `ccAsset`, or `cashWalletAsset`.                            |
| `payment_date`         | `ccAsset`      | Day of month (1–31) the credit card is paid; clamped to the month's last day.                        |
| `liability_type`       | liability      | `loan`, `mortgage`, or `debt`.                                                                       |
| `interest`             | liability      | Interest rate as a string (e.g. `"12"`), charged monthly.                                            |
| `opening_balance`      | all            | Starting balance as a string; pair it with `opening_balance_date`.                                  |
| `opening_balance_date` | all            | Date of the opening balance, `dd/mm/yyyy`.                                                           |
| `active`               | all            | `false` (default) creates the account but disables it and excludes it from net worth.               |
| `ignore`               | all            | `true` skips the account entirely (not created; its transactions are skipped). Defaults to `false`. |

**Settings** (all four required):

| Field                    | Description                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------ |
| `default_account_type`   | Type used when an account entry omits `type` (typically `asset`).                                |
| `default_account_role`   | Role used when an asset account omits `role` (typically `defaultAsset`).                          |
| `loan_payment_category`  | Firefly category that loan-*principal* transfers are booked under (loan payments to a liability).  |
| `loan_interest_category` | Firefly category that loan-*interest* transfers are booked under.                                 |

See [`firefly/config.py`](firefly/config.py) for the underlying dataclasses.

### Helper script

[`update_firefly.sh`](update_firefly.sh) is a convenience wrapper that ships a CSV to a remote
host over SSH and runs import + export there. It's designed to be installed onto your `PATH`
(e.g. `~/.local/bin`), so it reads its settings from a dedicated config file rather than from a
`.env` beside the script. Copy [`update_firefly.config.dist`](update_firefly.config.dist) into
place and fill it in:

```bash
mkdir -p ~/.config/moneywiz-to-firefly
cp update_firefly.config.dist ~/.config/moneywiz-to-firefly/config
```

The config file is looked up in this order (first match wins): `$MONEYWIZ_CONFIG`, then
`${XDG_CONFIG_HOME:-~/.config}/moneywiz-to-firefly/config`, then `./config` beside the script
(handy when running from a checkout). Settings can also be passed as plain environment
variables:

| Variable             | Description                                                       |
| -------------------- | ----------------------------------------------------------------- |
| `DEPLOY_SSH_HOST`    | SSH host: `user@host` or a `~/.ssh/config` alias                  |
| `DEPLOY_REMOTE_PATH` | Base dir on the host holding `reports/`, `db/`, and `config.json` |
| `DEPLOY_PROJECT_DIR` | Path to the `moneywiz-to-firefly` checkout on the host            |
| `DEPLOY_PATH_PREFIX` | Optional: dir to prepend to the host's `PATH` so `uv` is found (mise shims; empty = leave PATH as-is) |

Paths that should expand on the **host** (e.g. using `$HOME`) must be single-quoted in the
config so they aren't expanded locally — e.g. `DEPLOY_PROJECT_DIR='$HOME/moneywiz-to-firefly'`.
The host also needs its own Firefly credentials (`FIREFLY_URL` / `FIREFLY_TOKEN`, see
[`.env.dist`](.env.dist)) for the export step.

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
