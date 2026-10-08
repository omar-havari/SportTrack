# SportTrack

A sports stats pipeline that pulls football match/player data from two disagreeing sources
(football-data.org API + a Kaggle dataset), resolves players/teams across them despite
inconsistent names and IDs, and builds clean stats tables in SQLite.

> Work in progress

## Status

Phase 0 (environment setup) in progress.

## Setup

1. Create and activate a virtual environment (`.venv`)
2. `pip install -r requirements.txt`
3. Copy your football-data.org API key into `.env` as `FOOTBALL_DATA_API_KEY`

## Project structure

See `TASKS.md` for the full structure rationale.

## Data sources

- [football-data.org](https://www.football-data.org/) — match/fixture API
- A Kaggle football dataset (TBD — see `TASKS.md` Phase 1)

## Entity resolution approach

TBD — written up once Phase 5 is complete.
