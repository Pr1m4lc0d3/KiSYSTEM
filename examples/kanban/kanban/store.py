"""Persistence: load a board from a JSON file and save it back.

One responsibility: turn a file path into a Board and a Board into a file. It
owns the JSON encoding and the "no file yet" case, and nothing about board rules.
"""

import json
from pathlib import Path

from kanban.board import Board

# ===== Load =====


# Read a board from `path`. A missing file is a normal first run, not an error,
# so it yields a fresh empty board rather than raising.
def load_board(path: str) -> Board:
    file_path = Path(path)
    if not file_path.exists():
        return Board.empty()
    raw = file_path.read_text(encoding="utf-8")
    return Board.from_dict(json.loads(raw))


# ===== Save =====


# Write `board` to `path` as indented JSON. Parent directories are created so a
# user-supplied --file path in a new folder just works. Indented for a readable,
# diff-friendly, hand-inspectable file.
def save_board(path: str, board: Board) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(board.to_dict(), indent=2)
    file_path.write_text(text, encoding="utf-8")
