"""Display: turn a columns mapping into text for the terminal.

One responsibility: formatting. It reads the board's column order and produces a
string of three side-by-side columns. It performs no mutation and no I/O — the
caller prints whatever it returns.
"""

from kanban.board import COLUMNS
from kanban.models import Card

# ===== Layout constants =====

# Fixed column width keeps the three columns aligned regardless of content.
# Long titles are truncated to fit; the id is always preserved.
COLUMN_WIDTH = 28


# ===== Cell formatting =====


# Format one card as a single fixed-width cell line, e.g. "#3 Deploy [ops]".
# Truncates with an ellipsis so one long title can't break column alignment.
def _format_card(card: Card) -> str:
    label = f" [{card.label}]" if card.label else ""
    text = f"#{card.id} {card.title}{label}"
    if len(text) > COLUMN_WIDTH:
        text = text[: COLUMN_WIDTH - 1] + "…"
    return text.ljust(COLUMN_WIDTH)


# Build the full stack of lines for one column: a "TODO (n)" header, an underline,
# then one line per card (or a muted placeholder when the column is empty).
def _column_lines(name: str, cards: list[Card]) -> list[str]:
    header = f"{name.upper()} ({len(cards)})".ljust(COLUMN_WIDTH)
    underline = ("-" * len(name) + " " * COLUMN_WIDTH)[:COLUMN_WIDTH]
    body = [_format_card(card) for card in cards] or ["(empty)".ljust(COLUMN_WIDTH)]
    return [header, underline, *body]


# ===== Board assembly =====


# Render the whole board as three side-by-side columns. Shorter columns are
# padded so every row has all three cells aligned, then rows are joined top down.
def render_board(columns: dict[str, list[Card]]) -> str:
    blocks = [_column_lines(name, columns.get(name, [])) for name in COLUMNS]
    height = max(len(block) for block in blocks)
    blank = " " * COLUMN_WIDTH

    rows = []
    for row_index in range(height):
        cells = [block[row_index] if row_index < len(block) else blank for block in blocks]
        rows.append("  ".join(cells).rstrip())
    return "\n".join(rows)


# ===== Archive =====


# Render the archive of deleted cards as a simple top-down list: one line per
# card with its id, title, optional label, and deletion timestamp. The archive
# entries are plain dicts (from Board.to_dict), not Card objects, so this reads
# them by key. A friendly line stands in when nothing has been deleted yet.
def render_archive(archive: list[dict]) -> str:
    if not archive:
        return "Archive is empty — no cards have been deleted."

    lines = [f"ARCHIVE ({len(archive)} deleted)", "-------"]
    for entry in archive:
        label = f" [{entry['label']}]" if entry.get("label") else ""
        deleted = entry.get("deleted", "")
        lines.append(f"#{entry['id']} {entry['title']}{label}  (deleted {deleted})")
    return "\n".join(lines)
