# Design — Terminal Kanban Board CLI

A small, dependency-free Kanban board you drive from the terminal. Built under the
KiSYSTEM discipline: plan first, one responsibility per file, every unit bounded,
labeled, and self-documenting.

## Goal (verifiable condition)

A user can run, as separate process invocations:

```
python -m kanban --file board.json add "Write spec" --label docs
python -m kanban --file board.json move 1 doing
python -m kanban --file board.json list
python -m kanban --file board.json list --label docs
python -m kanban --file board.json remove 1
```

…and observe: cards land in `todo` on add; `move` relocates a card between
`todo`/`doing`/`done`; `list` renders three columns; `list --label L` shows only
cards with label `L`; `remove` deletes a card. State written by one invocation is
visible to the next — persistence survives across processes.

## Modules (one responsibility each)

| File | What it does | How it's used | Depends on |
|------|--------------|---------------|------------|
| `kanban/models.py` | Defines the `Card` record and its dict (de)serialization. | Created by the board; serialized by the store. | stdlib only |
| `kanban/board.py` | Holds board state (columns + id counter), the add/move/remove rules, and a read-only `filter_by_label` query. | The one object the CLI mutates. | `models` |
| `kanban/store.py` | Loads/saves a board to a JSON file; returns an empty board when the file is absent. | Called by the CLI at start and end. | `board` |
| `kanban/render.py` | Renders a columns mapping as aligned terminal columns. | Used by `list`. | `board` (column order) |
| `kanban/cli.py` | Parses args (argparse) and dispatches to the board, store, and render. | Program entry logic. | all of the above |
| `kanban/__main__.py` | `python -m kanban` entry point; calls `cli.main()`. | How the user runs it. | `cli` |

Each file owns exactly one concern: a record, the rules (with a filter query), persistence,
display, and wiring. No file mixes two.

## Web interface (a second front end over the same core)

The web UI is a **new interface, not a new core**. It reuses `Board` (add/move/
remove rules) and `store` (`load_board`/`save_board`) exactly as the CLI does:
load the board, perform one action, save. The rules and persistence are touched
nowhere — the existing CLI commands are unchanged.

| File | What it does | How it's used | Depends on |
|------|--------------|---------------|------------|
| `kanban/webapi.py` | The four web actions (read/add/move/remove): load → one core call → save, returning `(status, payload)`. | Called by `web.py` per request. | `store` (→ `board`) |
| `kanban/web.py` | `http.server` transport: routes requests to `webapi` and serves the static files. No rules, no API logic — just HTTP. | Started by `cli serve`. | `webapi`, static |
| `kanban/static/index.html` | Page shell: add-card form + empty board container. | Served by `web.py`. | `style.css`, `app.js` |
| `kanban/static/style.css` | Board presentation: three side-by-side columns, card tiles. | Linked by the page. | — |
| `kanban/static/app.js` | Behaviour: fetch `/api/board`, render, and act; re-fetch after each action. | Loaded by the page. | the JSON API |
| `kanban/cli.py` | Adds a `serve` subcommand over the same `--file` board. | `python -m kanban serve`. | `web` |

API surface (all JSON, served by `web.py` over `webapi`):

- `GET /api/board` → the board via `Board.to_dict`.
- `POST /api/cards {title, label?}` → `Board.add`, save, return the card.
- `POST /api/cards/<id>/move {column}` → `Board.move`, save, return the card.
- `DELETE /api/cards/<id>` → `Board.remove`, save.

Pure standard library throughout (`http.server` + `json`): no Flask/Django and no
third-party dependency, matching the project's dependency-free discipline.

### Web UI — visual redesign (balanced, modern layout)

Goal (verifiable): the board renders as three **equal-width, equal-height** columns on a
desktop viewport (never 3-and-1, never ragged), stacks to a single column under ~720px, and
reads as a clean modern board — a centred app bar, column headers with a count badge, and card
tiles with a coloured label pill and a subtle hover lift.

Approach: a **presentation-only** change. The ragged layout came from `align-items: start`,
which sized each column to its own content; columns now stretch to equal height inside a fixed
three-column grid within a centred max-width container. No core, API, server, or CLI code is
touched.

Files touched (blast radius — presentation only):
- `kanban/static/style.css` — layout + modern column/card styling.
- `kanban/static/app.js` — `renderBoard` only: a nicer column header (display title + count
  badge) and a card-list wrapper. No API call, rule, or orchestration logic changed.
- `kanban/static/index.html` — unchanged (the shell is already correct).

Verify:
1. Load the page → exactly three equal-height columns side by side on a wide window.
2. Narrow the window below ~720px → columns stack to one, no horizontal scroll.
3. Add / move / delete still work and re-render (behaviour unchanged).

### Web UI — glass / techie theme

Goal (verifiable): the board reads as frosted-glass panels over a deep, softly-lit
backdrop, still legibly (light text, clear contrast); three equal-height columns that
stack under 720px; ambient motion honours `prefers-reduced-motion`.

Direction (intentional — not the generic dark + single-neon default):
- Palette: a deep indigo **aurora** backdrop (`#0b1020` with indigo/cyan/violet glows),
  not flat black. Text near-white `#e7ecf5` / muted `#9aa7bd`.
- Signature: the accent **encodes the flow** — each column carries a stage colour that
  progresses `todo` (slate, queued) → `doing` (cyan, active) → `done` (green, complete).
  Hue is information here, not decoration: you read progress by colour.
- Type: a monospace utility face (system mono stack) for column labels and count badges —
  the techie register — with the system sans for card titles. No web-font dependency.
- Glass: translucent panels (~6–12% white over the backdrop) with backdrop-blur, a hairline
  light border, and a soft stage-coloured glow per column; cards lift and brighten on hover.

Blast radius (presentation only): `kanban/static/style.css` **only**. index.html, app.js, the
core, API, server, and CLI are untouched (stage colours keyed off column order via `nth-child`).

Verify:
1. Frosted-glass columns over the aurora backdrop; card text clearly legible.
2. todo / doing / done carry distinct, progressing accent colours.
3. Three equal-height columns on desktop; stack to one under 720px.
4. With `prefers-reduced-motion`, the ambient backdrop drift is off.

## Archive (deleted-card history)

Goal (verifiable): deleting a card (CLI `remove` or the web ✕) no longer destroys it — the
card moves to an **archive** with a deletion timestamp, persisted in the board file and viewable
from both interfaces. `python -m kanban archive` lists deleted cards; the web UI shows an
"Archive" section. Deletion becomes recoverable history, not silent loss. (Restoring a card from
the archive is a deliberate follow-up, not part of this change.)

Frame / reuse (checked before writing — no twins): the deletion path already funnels through
`Board.remove` (both the CLI `remove` handler and the web `DELETE` action call it), so archiving
in that one method covers both interfaces. The board already serializes via `to_dict`/`from_dict`
through the existing `store`, and the web's `GET /api/board` already returns `to_dict()` — so the
archive rides existing persistence and the existing endpoint: **no new store, no new API**. The
creation-timestamp logic in `Card.new` is extracted to a shared `models.now_stamp()` and reused
for the deletion timestamp rather than duplicated.

Module changes (each keeps its single responsibility):

| File | Change |
|------|--------|
| `kanban/models.py` | Extract `now_stamp()` (UTC ISO-seconds); `Card.new` calls it; reused for the deleted-at stamp. |
| `kanban/board.py` | `Board` gains an `archive` list; `remove` appends `{…card, "deleted": now_stamp()}`; `empty`/`to_dict`/`from_dict` carry it. |
| `kanban/render.py` | `render_archive(archive)` — terminal view of deleted cards. |
| `kanban/cli.py` | An `archive` subcommand → load board, print `render_archive`. Read-only. |
| `kanban/static/index.html` | An `#archive` section below the board. |
| `kanban/static/app.js` | Render the archive from the board data already fetched (no new request). |
| `kanban/static/style.css` | Muted styling for the archive section. |

Blast radius (NOT touched): `store.py`, `webapi.py`, `web.py` — the archive flows
through existing serialization, the existing store, and the existing `/api/board`.

Verify:
1. `add` a card then `remove` it → `archive` lists it with a `deleted` timestamp; it's gone from the board.
2. The web ✕ on a card → the card leaves its column and appears in the web "Archive" section.
3. Reload in a separate process → the archive persists in `board.json`.
4. Existing `add` / `move` / `list` / `remove` / `serve` behave exactly as before.

## Interfaces

- `models.Card(id:int, title:str, label:str|None, created:str)`
  - `Card.new(card_id, title, label) -> Card`
  - `card.to_dict() -> dict` / `Card.from_dict(d) -> Card`
- `board.COLUMNS == ("todo", "doing", "done")`
- `board.Board(next_id:int, columns:dict[str, list[Card]])`
  - `Board.empty() -> Board`
  - `add(title, label) -> Card`  (always lands in `todo`)
  - `move(card_id, column) -> Card`  (raises on unknown id/column)
  - `remove(card_id) -> Card`  (raises on unknown id)
  - `to_dict()` / `Board.from_dict(d)`
- `store.load_board(path) -> Board` / `store.save_board(path, board) -> None`
- `board.filter_by_label(columns, label) -> dict[str, list[Card]]` (a board query, not its own file)
- `render.render_board(columns) -> str`
- `cli.main(argv=None) -> int`

## Build sequence (each step has a verify check)

1. `models.py` — Card + (de)serialization.
   verify: `Card.new(1,"t",None)` round-trips through `to_dict`/`from_dict`.
2. `board.py` — COLUMNS, Board, add/move/remove.
   verify: add lands in todo; move relocates; remove deletes; bad id/column raise.
3. `store.py` — JSON load/save; missing file → empty board.
   verify: save then load returns an equal board; absent path → empty board.
4. `board.filter_by_label` — label filter (a board query, not its own file).
   verify: filtering keeps only matching-label cards, preserves column keys.
5. `render.py` — column display.
   verify: output contains all three column headers and a known title.
6. `cli.py` + `__main__.py` — argparse + dispatch.
   verify: end-to-end commands from the Goal run and persist across processes.
