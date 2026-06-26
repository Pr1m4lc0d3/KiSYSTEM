"""Web API actions: translate JSON API intents into core board operations.

One responsibility: the four board actions the web UI exposes — read, add, move,
remove. Each loads the board, performs exactly one core operation, persists when
it changed state, and returns a (status, payload) pair. It owns no HTTP, sockets,
or routing (web.py handles transport) and no board rules (those live in Board);
it is the thin seam that reuses the existing core through the existing store.
"""

from kanban.store import load_board, save_board

# ===== Read =====


# Return the whole board as a JSON-ready dict via Board.to_dict. Read-only, so it
# never saves — GET must not mutate state.
def get_board(board_file: str) -> tuple[int, dict]:
    board = load_board(board_file)
    return 200, board.to_dict()


# ===== Mutations =====


# Add a card from a {title, label?} payload and persist. A blank/missing title is
# rejected (400) here because a titleless card has nothing to show or act on; the
# landing column is the core's decision (always todo), never the caller's.
def add_card(board_file: str, payload: dict) -> tuple[int, dict]:
    title = (payload.get("title") or "").strip()
    if not title:
        return 400, {"error": "title is required"}
    label = (payload.get("label") or "").strip() or None
    board = load_board(board_file)
    card = board.add(title, label)
    save_board(board_file, board)
    return 201, card.to_dict()


# Move a card to a {column} and persist. The core owns the rules, so we just
# translate its exceptions into HTTP-shaped errors: unknown column → 400 (bad
# request), unknown id → 404 (no such card).
def move_card(board_file: str, card_id: int, payload: dict) -> tuple[int, dict]:
    column = payload.get("column", "")
    board = load_board(board_file)
    try:
        card = board.move(card_id, column)
    except ValueError as error:
        return 400, {"error": str(error)}
    except KeyError as error:
        return 404, {"error": str(error)}
    save_board(board_file, board)
    return 200, card.to_dict()


# Delete a card by id and persist. An unknown id is the only failure the core can
# raise here, mapped to 404 so the client learns the card was already gone.
def remove_card(board_file: str, card_id: int) -> tuple[int, dict]:
    board = load_board(board_file)
    try:
        card = board.remove(card_id)
    except KeyError as error:
        return 404, {"error": str(error)}
    save_board(board_file, board)
    return 200, {"removed": card.id}
