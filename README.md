# EasyMoney Macro Evidence Prototype — v0.1

## What this is
A read-only, free-source ingestion prototype for five representative FRED series. It stores the observation date, the vintage bounds returned by FRED, the UTC retrieval time, source identifiers, and missing-data flags.

## What it is not
It does not calculate EasyMoney's 1–5 scores, interpret the dominant driver, generate CANDIDATE/WATCH/PASS, validate all five gates, or supply execution signals. FRED series are example candidates, not proof that these series satisfy all workbook definitions. Fed total assets are not equivalent to net liquidity.

## Run
1. Request a free API key: https://fred.stlouisfed.org/docs/api/api_key.html
2. Set the `FRED_API_KEY` environment variable.
3. Run `python easymoney_macro_ingest.py 2026-11-05` (or another date).
4. Inspect the generated JSON file and the per-series status fields.

## Verification caveat
A FRED historical vintage date is **not** a substitute for the original intraday publication timestamp. For historical replay, separately validate release times, initial prints, revisions, source definitions, frequency, and the data available before each cutoff. A live endpoint test has not been performed in this environment.

## Test
Run `python -m unittest test_ingest.py`.

## Freshness checks (v0.2)
After collecting a JSON snapshot, run `python freshness.py <snapshot.json>` to produce a separate machine-readable freshness report. This checks data presence and observation ages, **not** release-to-ingestion latency or intraday quote validity. Until publication-time validation and authorized live market feeds exist, `research_ready` remains false and `live_intraday_market_data_verified` remains false. No real-time claim is made.

## Official Treasury yield CSV importer (v0.3)
`treasury_yields.py` parses the US Treasury's daily par yield curve CSV export (columns such as `Date`, `2 Yr`, `10 Yr`). It validates dates, duplicates, numeric ranges, and missing tenors, and saves the SHA-256 of the original file. Run `python treasury_yields.py treasury.csv treasury_evidence.json` with an authentic downloaded CSV. It does not download data automatically, assert publication timestamps, calculate a macro score, or provide intraday futures quotes.

Run all ten controlled-input tests with `python -m unittest discover -v`.

**Connection status:** No successful live network call has been made. The environment could not resolve the Treasury host during a connectivity attempt. FRED still requires a user's free API key. No live market-data service or hosted iPhone dashboard is running.

## Official-source retrieval and evidence archive (v0.4)
`collect_treasury.py` can retrieve an explicitly configured HTTPS CSV export URL from an allowlisted official US Treasury host, parse it using the existing validator, and persist the entire received evidence record to a local SQLite database. `evidence_store.py` retains the capture timestamp, observation cutoff, content hash, and full JSON. Repeated identical payloads are deduplicated. This is local persistence, **not a deployed or continuously running service**. Supply an actual verified official CSV URL; the collector does not discover endpoints or assert that a URL is currently operational.

Example: `python collect_treasury.py --url 'https://home.treasury.gov/<verified-csv-path>' --db evidence.sqlite3`

Run all 14 controlled-input tests: `python -m unittest discover -v`. The new retrieval test mocks the network. No actual live endpoint success or freshness has been demonstrated. No trading status, macro score, or execution signal is generated.

## Archive health report (v0.5)
Run `python health_report.py --db evidence.sqlite3` to see which sources have saved evidence, the age of the last retrieval, and the age of the underlying observation. Missing archives show no data. Future capture timestamps are flagged. This does not establish publication latency, actual feed availability, or readiness to trade. The report deliberately leaves `research_ready` and `live_intraday_market_data_verified` false. Run `python -m unittest discover -v` for the complete controlled-input test suite.

## v0.7: Scheduled evidence publishing (not deployed)
`publish_treasury.py` fetches the official Treasury XML for the current month, validates and archives it, then atomically publishes `docs/treasury.json`. A GitHub Actions workflow runs it at 23:15 UTC on weekdays, with a manual trigger. A static, mobile-friendly verification page in `docs/index.html` reads that JSON and distinguishes daily data from live futures quotes. The repository owner must publish this directory using GitHub Pages (Settings > Pages > Deploy from a branch > main > /docs) and enable workflow write permissions. Some repositories may have organization restrictions on GitHub Pages or workflow pushes. A failed fetch preserves the previous snapshot; the page will flag stale retrievals after 36 hours. The archive SQLite file is local to each workflow run and is NOT persisted in GitHub Actions; persistent hosted archival storage remains future work. This is a deployment-ready source-verification prototype, not the completed EasyMoney intelligence dashboard. No live source response has been verified in this environment; the Treasury feed format may change. Run `python -m unittest discover -q` for 24 controlled-input tests.

## v0.8: Durable public evidence history (not deployed)
The scheduled publisher now writes each validated snapshot into `docs/history/YYYY-MM/` under a source-hash-based filename. The workflow commits the archive together with `docs/treasury.json`, so snapshots survive between GitHub Actions runs (unlike the runner's local SQLite database). Identical observations are deduplicated; conflicting content under the same evidence key fails safely. This is an audit trail of retrieved snapshots, **not** point-in-time verification of the Treasury's actual release time. It is a public archive when GitHub Pages is enabled; do not store private account or trading data there. The user still needs to connect a repository and enable Actions/Pages for a real deployment. No live retrieval has been verified here.

## v0.10 — Treasury curve context (not a completed gate)
`cross_asset_assessment.py` uses only timestamped official daily nominal Treasury par yields. It computes 10Y–2Y and 10Y–3M spreads in basis points when observations pass basic checks. Older than four calendar days is marked stale. Missing/future timestamps remain unverified. It never passes the Cross-Asset gate or assigns a Weekly Regime score. A GitHub Actions job can publish the assessment with the existing Treasury snapshot after deployment. This does not verify live collection, current market prices, or real yields.

## v0.21 — Partial-source snapshot integrity (local tests only)
A partial FRED collection now retains previously captured factor records while preserving each record's original `retrieved_at_utc` timestamp. The integrity validator evaluates each factor against its own retrieval time, so a freshly downloaded Inflation record cannot make an older Growth record appear fresh. The collection receipt still describes only the latest attempted download, not the merged number of rows. The mobile preview exposes per-factor status. No data is assigned an original release timestamp, macro score, or gate pass. Run `python -m unittest discover -q`. No live host or deployment was verified.
