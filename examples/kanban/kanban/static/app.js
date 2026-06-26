// app.js — the board UI's behaviour: fetch state, render it, and act on it.
// One responsibility: turn the JSON API into a live three-column board. It owns
// no rules — the server (Board) decides what is legal; this only calls the API
// and redraws whatever the server returns as the single source of on-screen truth.

// ===== Constants =====

// Column order must mirror the server's COLUMNS so "move left/right" maps onto the
// same flow the CLI enforces: todo -> doing -> done.
const COLUMNS = ["todo", "doing", "done"];

// Human-friendly titles for the column headers (the API uses the lowercase keys).
const COLUMN_TITLES = { todo: "To Do", doing: "Doing", done: "Done" };

// ===== API calls =====
// Thin wrappers over fetch. Each resolves only after the server has saved, so the
// caller can then refresh from the authoritative board state.

async function fetchBoard() {
  const res = await fetch("/api/board");
  return res.json();
}

async function addCard(title, label) {
  await fetch("/api/cards", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, label }),
  });
}

async function moveCard(id, column) {
  await fetch(`/api/cards/${id}/move`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ column }),
  });
}

async function deleteCard(id) {
  await fetch(`/api/cards/${id}`, { method: "DELETE" });
}

// ===== Rendering =====

// Build one card tile: title, optional label, and move/delete controls. The move
// buttons are disabled at the ends of the flow so the UI never asks for an
// out-of-range column the server would refuse anyway.
function renderCard(card, columnIndex) {
  const tile = document.createElement("div");
  tile.className = "card";

  const title = document.createElement("div");
  title.className = "card-title";
  title.textContent = card.title; // textContent, not innerHTML — titles are data, not markup
  tile.appendChild(title);

  if (card.label) {
    const label = document.createElement("span");
    label.className = "card-label";
    label.textContent = card.label;
    tile.appendChild(label);
  }

  const controls = document.createElement("div");
  controls.className = "card-controls";

  const left = document.createElement("button");
  left.textContent = "←"; // left arrow
  left.title = "Move left";
  left.disabled = columnIndex === 0;
  left.onclick = () => act(() => moveCard(card.id, COLUMNS[columnIndex - 1]));

  const right = document.createElement("button");
  right.textContent = "→"; // right arrow
  right.title = "Move right";
  right.disabled = columnIndex === COLUMNS.length - 1;
  right.onclick = () => act(() => moveCard(card.id, COLUMNS[columnIndex + 1]));

  const del = document.createElement("button");
  del.textContent = "✕"; // multiplication x
  del.title = "Delete";
  del.className = "delete";
  del.onclick = () => act(() => deleteCard(card.id));

  controls.append(left, right, del);
  tile.appendChild(controls);
  return tile;
}

// Draw the whole board: one column section per COLUMN, each with a header (display
// title + count badge) and a scrollable list of its cards. It replaces the board's
// contents wholesale — the simplest correct redraw, and the board is far too small
// for partial updates to matter.
function renderBoard(board) {
  const root = document.getElementById("board");
  root.replaceChildren(); // clear without innerHTML — no markup ever parsed from data
  COLUMNS.forEach((name, index) => {
    const cards = board.columns[name] || [];

    const column = document.createElement("section");
    column.className = "column";

    // Header: friendly title on the left, a count badge on the right.
    const head = document.createElement("div");
    head.className = "column-head";
    const titleSpan = document.createElement("span");
    titleSpan.textContent = COLUMN_TITLES[name] || name;
    const count = document.createElement("span");
    count.className = "count";
    count.textContent = cards.length;
    head.append(titleSpan, count);
    column.appendChild(head);

    // Cards live in their own list so the column header stays fixed at the top.
    const list = document.createElement("div");
    list.className = "card-list";
    cards.forEach((card) => list.appendChild(renderCard(card, index)));
    column.appendChild(list);

    root.appendChild(column);
  });
}

// Draw the archive of deleted cards from the SAME board object already fetched
// for the columns (board.archive arrives inside /api/board's to_dict) — no extra
// request, no new endpoint. Rendered on every refresh so a delete shows here at
// once. Archive entries are plain records: id, title, optional label, deleted-at.
function renderArchive(board) {
  const root = document.getElementById("archive");
  root.replaceChildren(); // clear without innerHTML — no markup ever parsed from data
  const entries = board.archive || [];

  const head = document.createElement("h2");
  head.className = "archive-head";
  head.textContent = `Archive (${entries.length})`;
  root.appendChild(head);

  if (entries.length === 0) {
    const empty = document.createElement("p");
    empty.className = "archive-empty";
    empty.textContent = "No cards have been deleted.";
    root.appendChild(empty);
    return;
  }

  const list = document.createElement("div");
  list.className = "archive-list";
  entries.forEach((entry) => {
    const row = document.createElement("div");
    row.className = "archive-item";

    const title = document.createElement("span");
    title.className = "archive-title";
    title.textContent = `#${entry.id} ${entry.title}`; // textContent — data, not markup
    row.appendChild(title);

    if (entry.label) {
      const label = document.createElement("span");
      label.className = "archive-label";
      label.textContent = entry.label;
      row.appendChild(label);
    }

    const deleted = document.createElement("span");
    deleted.className = "archive-deleted";
    deleted.textContent = entry.deleted || "";
    row.appendChild(deleted);

    list.appendChild(row);
  });
  root.appendChild(list);
}

// ===== Orchestration =====

// Pull the latest board from the server and redraw both the columns and the
// archive from that one payload. On-screen state is always whatever /api/board
// returns, never local guesswork.
async function refresh() {
  const board = await fetchBoard();
  renderBoard(board);
  renderArchive(board);
}

// Run an action, then refresh. Centralizing "act then redraw" keeps every button
// handler a one-liner and guarantees the view re-syncs after every change.
async function act(action) {
  await action();
  await refresh();
}

// ===== Wiring =====

// Wire the add-card form and paint the initial board once the DOM is ready.
function init() {
  const form = document.getElementById("add-form");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const title = form.title.value.trim();
    if (!title) return; // mirror the server's title-required rule; nothing to add
    const label = form.label.value.trim();
    act(async () => {
      await addCard(title, label);
      form.reset();
      form.title.focus();
    });
  });
  refresh();
}

document.addEventListener("DOMContentLoaded", init);
