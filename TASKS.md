# SportTrack — Task Roadmap

**Goal:** Pull football match/player data from two different sources (football-data.org API + a Kaggle dataset), reconcile the fact that they disagree on player names/IDs/team names, and produce clean, queryable stats tables. The centerpiece skill is **entity resolution** (matching "the same player" across two messy sources) — that's what goes on your resume/portfolio, so don't rush that phase.

**Stack:** Python + pandas + SQLite. Everything runs locally, no servers to manage. SQLite gives you real SQL practice without infra overhead.

**Scope:** Portfolio-sized. Scripted pipeline (not a scheduler), 2 sources, strong focus on matching logic + clean final tables + a write-up. No Airflow/dbt/CI for v1 — those are listed as optional stretch goals at the bottom if you want to go further later.

How to use this file: work top to bottom, phase by phase. Each phase has a checklist, a short "why this matters" note, and a "concepts to learn" list — those are things to go read a short article/doc about before doing the step, since you said you're new to this. Don't write any code until you and I have talked through the phase you're on — this file is the map, not the implementation.

---

## Phase 0 — Environment & Project Setup

- [x] Install Python (3.11+) and confirm `pip`/`venv` work
- [ ] Create a virtual environment for this project
- [ ] Decide on project folder structure, e.g.:
  ```
  data/
    raw/          <- untouched downloaded files, never edited by hand
    interim/      <- cleaned-but-not-merged data
    processed/    <- final matched/merged tables
  src/            <- scripts/modules
  notebooks/      <- exploration (Jupyter)
  tests/          <- data validation tests
  sql/            <- schema definitions, queries
  ```
- [ ] Set up `requirements.txt` (pandas, requests, jupyter, rapidfuzz, pytest — add as needed)
- [ ] Initialize `.gitignore` (ignore `data/raw`, `.env`, venv folder, `*.db`)
- [ ] Create a `.env` file (git-ignored) for the football-data.org API key — never commit API keys
- [ ] Add a basic `README.md` stub (you'll flesh this out in Phase 9)

**Why this matters:** Separating `raw` from `interim`/`processed` is a core data-engineering habit — it means you can always blow away your processed data and rebuild it from raw without re-downloading anything. This is the difference between a script and a *pipeline*.

**Concepts to learn:** virtual environments, `.gitignore` basics, why raw data should be immutable/"write-once".

---

## Phase 1 — Pick & Access Your Data Sources

- [ ] Sign up for a free football-data.org API key
- [ ] Explore the football-data.org API docs — identify endpoints for: competitions, teams, matches, players
- [ ] Decide which competition(s)/season(s) to pull (keep it small for v1 — e.g. one league, one season)
- [ ] Find a Kaggle football dataset that overlaps the same league/season (player stats or match stats)
- [ ] Download the Kaggle dataset manually and inspect it (don't automate this yet)
- [ ] Write down, in plain English, what each source gives you and what it's missing (e.g. "API has fixtures + scores but thin player stats; Kaggle has rich player stats but no live fixtures")
- [ ] Confirm there's actually meaningful overlap between the two sources (same players/teams/season) — if not, pick different data before building anything

**Why this matters:** This is the step people skip and regret. If your two sources don't actually describe overlapping players/matches, there's nothing to "merge" and the whole project's premise collapses.

**Concepts to learn:** reading API docs, rate limits, what an API key/auth header is, CSV vs JSON shapes.

---

## Phase 2 — Raw Data Ingestion

- [ ] Write a script to call the football-data.org API and save raw JSON responses to `data/raw/` (one file per endpoint/competition/season — timestamp or version the filenames)
- [ ] Write a script to copy/load the Kaggle CSV(s) into `data/raw/` in a consistent way
- [ ] Add basic error handling: what happens if the API rate-limits you or returns an error?
- [ ] Log how many rows/records you pulled from each source (sanity check number)
- [ ] Decide: is this a one-time pull or do you want it re-runnable? (For v1, re-runnable but manually triggered is enough.)

**Why this matters:** "Ingestion" should be dumb and reliable — just get the data and save it exactly as received. All the smart logic (cleaning, matching) happens later, on a copy. This separation makes debugging much easier later ("is the bug in my ingestion or my cleaning?").

**Concepts to learn:** idempotency (running a script twice shouldn't corrupt things), basic logging, JSON → tabular conversion.

---

## Phase 3 — Data Exploration & Profiling

- [ ] In a notebook, load both raw sources and look at them side by side
- [ ] For each source, profile: row counts, missing values, duplicate rows, data types, date formats
- [ ] Specifically look at how each source represents: player names, player IDs, team names, team IDs, dates
- [ ] Write down every discrepancy you find, e.g.:
  - "API uses full name 'Kevin De Bruyne', Kaggle uses 'K. De Bruyne'"
  - "API team IDs are numeric, Kaggle uses team name as key"
  - "Accents/diacritics differ (José vs Jose)"
  - "Suffixes/nicknames (Jr., known-as names)"
  - "Transferred players appearing under different teams in each source"
- [ ] This discrepancy list becomes your spec for Phase 5 (matching) — don't skip documenting it

**Why this matters:** You cannot design a good matching strategy until you've actually looked at *why* the sources disagree. Jumping straight to fuzzy-matching code without this step is how people build the wrong solution.

**Concepts to learn:** data profiling, `.info()`/`.describe()` in pandas, what "dirty data" typically looks like.

---

## Phase 4 — Target Schema Design

- [ ] Sketch (on paper or in a doc, not code) the tables you want at the end, e.g.:
  - `dim_player` (one row per real-world player, with a stable internal `player_id`)
  - `dim_team`
  - `fact_match` (one row per match)
  - `fact_player_match_stats` (one row per player per match: minutes, goals, etc.)
- [ ] Decide on your own internal surrogate keys (don't rely on either source's ID as the "real" ID)
- [ ] Map each source's fields onto this schema — note what's missing from each source
- [ ] Decide how you'll store the *mapping* from source IDs → your internal ID (a `player_id_map` table that says "football-data.org id=44 AND kaggle name='K. De Bruyne' → internal_player_id=1001")

**Why this matters:** This is basic data warehouse modeling (star-schema style: dimensions + facts). Designing the target shape *before* writing merge code prevents you from building a tangled mess that only works for the two sources you have today.

**Concepts to learn:** star schema (fact vs dimension tables), surrogate keys vs natural keys, crosswalk/mapping tables.

---

## Phase 5 — Entity Resolution (the core skill) 🎯

This is the phase to spend the most time on and the one to be able to talk about in an interview. Break it into these sub-steps:

### 5a. Blocking (narrow the search space)
- [ ] Decide a cheap first-pass filter to avoid comparing every player to every player (e.g. same team, or same nationality, or same first-letter-of-surname)
- [ ] Understand why you need this: comparing N×M players directly is wasteful and increases false matches

### 5b. Normalization
- [ ] Define a consistent name-normalization function (lowercase, strip accents/diacritics, strip punctuation, handle "Jr."/"Sr.", standardize initials)
- [ ] Normalize team names similarly (e.g. "Man United" vs "Manchester United")
- [ ] Normalize dates and numeric fields the same way across sources

### 5c. Candidate matching
- [ ] Try exact match first on normalized names + team — see how much this resolves on its own
- [ ] For the unmatched remainder, apply fuzzy string matching (e.g. token-sort/Levenshtein-based similarity) between candidate pairs from the blocking step
- [ ] Add secondary signals beyond name: team, nationality/position, date of birth if available — a name match alone is weak (common names, multiple "J. Silva"s)
- [ ] Produce a similarity score per candidate pair, not just a yes/no

### 5d. Thresholding & review
- [ ] Pick a similarity threshold above which you auto-accept a match
- [ ] Pick a lower threshold below which you auto-reject
- [ ] For the ambiguous middle band, manually review and resolve by hand (this is normal and expected — document how many fell here)
- [ ] Watch for **transfers**: a player who switched teams mid-season may look unmatched if you blocked too hard on "same team"

### 5e. Build the crosswalk table
- [ ] Persist your final decisions into the `player_id_map` table from Phase 4 (source → internal ID)
- [ ] Record the match method and confidence score per row, not just the final ID (you'll want this for debugging/auditing later)
- [ ] Do the same exercise for teams (usually much easier — fewer entities, clearer names)

### 5f. Measure your own matching quality
- [ ] Hand-label a small sample (e.g. 30–50 players) with the *correct* match yourself
- [ ] Compute precision/recall of your matcher against that labeled sample
- [ ] Note false positives (wrongly merged two different players) vs false negatives (missed a real match) — explain the tradeoff

**Why this matters:** This whole phase *is* the "skill employers value" the project is built around. Treat it like the deliverable, not a chore blocking the "real" work.

**Concepts to learn:** record linkage / entity resolution basics, blocking, edit distance (Levenshtein) vs token-based similarity, precision/recall, why fuzzy matching alone is unreliable without secondary attributes.

---

## Phase 6 — Build the Cleaned & Merged Tables

- [ ] Using the crosswalk tables from Phase 5, join the two sources into your Phase 4 schema
- [ ] Decide conflict-resolution rules when both sources disagree on a *value* (not just identity) — e.g. different goal counts for the same match. Document which source wins and why, per field.
- [ ] Handle players/matches that exist in only one source (don't silently drop them — decide and document: keep with nulls? exclude? flag?)
- [ ] Load the merged, cleaned tables into a local SQLite database
- [ ] Write basic SQL constraints (primary keys, not-null) on the SQLite tables where appropriate

**Why this matters:** This is standard ETL "transform + load." The interesting decisions here are the conflict-resolution rules — be ready to explain *why* you chose source A over source B for a given field.

**Concepts to learn:** basic SQL DDL (CREATE TABLE, keys), merge/join semantics (inner vs left vs outer join) and what each choice means for your row counts.

---

## Phase 7 — Build the Stats Tables

- [ ] Write SQL queries (or pandas groupby) to produce the actual "stats tables" deliverable, e.g.:
  - Player season totals (goals, assists, minutes, appearances)
  - Team standings/form table
  - Per-90-minutes normalized stats
  - Head-to-head or home/away splits
- [ ] Store these as views or materialized tables in SQLite, separate from the raw fact tables
- [ ] Sanity-check a few numbers by hand against a public source (e.g. does your top scorer match what's publicly reported?)

**Why this matters:** This is the "so what" of the project — turning matched/cleaned data into something a user/analyst would actually query. Sanity-checking against a known public number is your test that the whole pipeline (ingestion → matching → merge) didn't quietly corrupt the data.

**Concepts to learn:** SQL `GROUP BY`/window functions, SQL views vs tables.

---

## Phase 8 — Data Quality & Testing

- [ ] Write simple automated checks (pytest or plain assertions) that run after the pipeline, e.g.:
  - No duplicate `player_id` in `dim_player`
  - No match with negative minutes played
  - Row counts within expected range
  - Every `fact_player_match_stats` row has a valid `player_id` and `match_id` (referential integrity)
- [ ] Re-run your precision/recall check from 5f as an automated regression test, so future changes to the matcher can't silently get worse
- [ ] Write down known limitations (e.g. "doesn't handle a player who changed their registered name mid-career")

**Why this matters:** This is what separates "a script that worked once" from "a pipeline" — tests that catch regressions when you touch the matching logic later.

**Concepts to learn:** basic pytest, what "referential integrity" means, regression testing for data.

---

## Phase 9 — Documentation & Portfolio Polish

- [ ] Write a proper `README.md`: problem statement, data sources, architecture diagram (even a simple ASCII one), how to run it
- [ ] Explicitly call out the entity-resolution approach and your precision/recall numbers — this is the part to highlight for employers
- [ ] Include a few example queries/outputs (screenshots or markdown tables) showing the final stats tables
- [ ] Note what you'd do differently/next with more time (shows maturity)
- [ ] Push to GitHub with a clean commit history (not one giant commit)

**Why this matters:** Unreviewed, undocumented code doesn't read as a portfolio piece. The write-up is often what a reviewer actually reads before they read any code.

---

## Stretch Goals (optional, after v1 works end-to-end)

- [ ] Add a 3rd data source and extend the matching logic to N-way matching
- [ ] Automate incremental ingestion (only pull new matches since last run) instead of full re-pulls
- [ ] Add orchestration (Airflow/Prefect/Dagster) to schedule the pipeline
- [ ] Swap SQLite for Postgres and containerize with Docker
- [ ] Add a small dashboard (e.g. Streamlit) on top of the stats tables
- [ ] Try a proper record-linkage library (e.g. `recordlinkage` or `splink`) instead of hand-rolled fuzzy matching, and compare results
- [ ] Add CI (GitHub Actions) to run your Phase 8 tests on every push

---

## Working Agreement

- I will not write code until you tell me which phase/step you're ready to start and give explicit go-ahead.
- When you're ready for a phase, tell me the phase number and we'll scope that step's code together.
- Check items off as you go — tell me when you want this file updated.
