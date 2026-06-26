# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Deleted-card **archive** — `remove` (CLI and the web ✕) no longer destroys a
  card: `Board.remove` appends a copy stamped with a `deleted` time to a new
  `Board.archive`, carried through `empty`/`to_dict`/`from_dict` so it persists in
  the board file. A new `python -m kanban archive` subcommand (`render_archive` in
  `render.py`) lists deleted cards in the terminal, and the web UI gains an
  `#archive` section (`index.html`/`app.js`/`style.css`) rendered from the board
  data already returned by `GET /api/board` — so deletion becomes recoverable
  history with no new store, endpoint, or fetch. `models.now_stamp()` was extracted
  from `Card.new` and reused for the deletion timestamp. (`store.py`, `filters.py`,
  `webapi.py`, `web.py` untouched.)
- `kanban/webapi.py` — the four web actions (read/add/move/remove) as a thin seam
  over the existing `Board` + `store`, so the web UI reuses the core's rules and
  persistence instead of reimplementing them, and HTTP stays out of the rules.
- `kanban/web.py` — a dependency-free `http.server` that serves the static page
  and a JSON API (`GET /api/board`, `POST /api/cards`, `POST /api/cards/<id>/move`,
  `DELETE /api/cards/<id>`), so the board is usable in a browser with no framework.
- `kanban/static/index.html` · `style.css` · `app.js` — a vanilla three-column
  board: an add-card form and per-card move-left/right and delete controls that
  re-fetch `/api/board` after every action, so the view always mirrors saved state.
- `kanban/cli.py` — a `serve` subcommand (`python -m kanban serve [--port]`) that
  starts the web UI over the same `--file` board, so the new interface is one more
  thin wire alongside the existing commands, which are unchanged.
- `design.md` — the plan written before any code: goal, one-responsibility module
  table, interfaces, and a verify-stepped build sequence (KiSYSTEM: plan first).
- `kanban/models.py` — the `Card` record with timestamped creation and dict
  (de)serialization, so persistence has a stable, mirrored shape to round-trip.
- `kanban/board.py` — `COLUMNS` plus the `Board` rules (add/move/remove) with a
  single `_take` helper, so every column/id invariant is enforced in one place.
- `kanban/store.py` — JSON load/save with "missing file → empty board", so a
  first run needs no setup and the saved file stays human-readable.
- `kanban/filters.py` — pure label filter that preserves all column keys, so the
  rendered board keeps its three-column shape when narrowed to one label.
- `kanban/render.py` — fixed-width side-by-side column rendering, so the board
  reads as a real Kanban board in the terminal with aligned columns.
- `kanban/cli.py` — argparse surface and load → act → save dispatch, so each
  command stays a thin wire between the terminal and the rules.
- `kanban/__main__.py` / `kanban/__init__.py` — `python -m kanban` entry point,
  so the tool runs as a standard, dependency-free Python module.

### Changed
- **Folded `filters.py` into a `board.py` "Queries" section** (`filter_by_label` is now a
  board query; `filters.py` removed, CLI import rewired, behaviour unchanged). A single
  22-line function used in one place is a section, not its own file — applying KiSYSTEM's
  corrected modularity rule: prefer a section to a one-function file; minimize files subject
  to clarity.
- `kanban/static/style.css` + `app.js` (`renderBoard` only) — redesigned the web
  board to three equal-width, **equal-height** columns in a centred container (it was
  ragged because columns sized to their own content), with a modern treatment: count
  badges, label pills, card hover-lift, and single-column stacking under 720px.
  Presentation only — no core, API, server, or CLI code touched.
- `kanban/static/style.css` — glass/techie theme: frosted backdrop-blur panels over a
  deep indigo aurora, with the per-column accent **encoding flow** (todo slate → doing
  cyan → done green), monospace labels, and an ambient drift that honours
  `prefers-reduced-motion`. Stage colours key off column order (`nth-child`), so app.js
  stays untouched. Presentation only.

### Fixed
- `kanban/static/style.css` — the column's top accent was a hard `border-top` that got
  clipped at the rounded corners; it's now an inset top line + glow that follows the radius.
- `kanban/static/style.css` — the top card in each column had its hover glow clipped by the
  card-list's `overflow` (it cropped the top edge); removed the overflow clip so card glows
  render fully.
