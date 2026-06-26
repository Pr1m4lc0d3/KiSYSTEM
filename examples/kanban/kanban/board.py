"""The board's state and its rules: add, move, remove.

One responsibility: hold the three columns plus the id counter, and enforce the
rules for changing them. It knows nothing about files, argument parsing, or how
the board is displayed — those live in store, cli, and render.
"""

from kanban.models import Card, now_stamp

# ===== Constants =====

# The canonical column set and their fixed left-to-right order. This tuple is
# the single source of truth other modules import rather than re-listing names.
COLUMNS: tuple[str, ...] = ("todo", "doing", "done")


# ===== Board =====


class Board:
    """The whole board: a monotonically increasing id counter, one ordered list
    of cards per column, and an archive of deleted cards. All mutations go through
    add/move/remove so the invariants (unique ids, valid columns) hold in one place."""

    def __init__(
        self,
        next_id: int,
        columns: dict[str, list[Card]],
        archive: list[dict] | None = None,
    ):
        self.next_id = next_id
        self.columns = columns
        # Default to a fresh list rather than a shared mutable default arg.
        self.archive = archive if archive is not None else []

    # An empty board with every known column present and an empty archive. Used
    # for a brand-new file.
    @classmethod
    def empty(cls) -> "Board":
        return cls(next_id=1, columns={name: [] for name in COLUMNS}, archive=[])

    # ===== Mutations =====

    # Create a card and place it in `todo`. New work always enters at the start
    # of the flow, so callers never choose the landing column.
    def add(self, title: str, label: str | None = None) -> Card:
        card = Card.new(self.next_id, title, label)
        self.next_id += 1
        self.columns["todo"].append(card)
        return card

    # Relocate a card to another column. Validates the target up front so an
    # invalid column name fails loudly instead of silently dropping the card.
    def move(self, card_id: int, column: str) -> Card:
        if column not in self.columns:
            raise ValueError(
                f"unknown column '{column}'; choose one of {', '.join(COLUMNS)}"
            )
        card = self._take(card_id)
        self.columns[column].append(card)
        return card

    # Delete a card from wherever it lives. The card is not lost: a copy stamped
    # with the deletion time is appended to the archive so removal is recoverable
    # history. Returns the removed card so callers can report what was deleted.
    def remove(self, card_id: int) -> Card:
        card = self._take(card_id)
        self.archive.append({**card.to_dict(), "deleted": now_stamp()})
        return card

    # ===== Internal helpers =====

    # Find a card by id, detach it from its column, and return it. Centralizes
    # the "locate and unlink" step shared by move and remove, and is the single
    # spot that raises on an unknown id.
    def _take(self, card_id: int) -> Card:
        for cards in self.columns.values():
            for index, card in enumerate(cards):
                if card.id == card_id:
                    return cards.pop(index)
        raise KeyError(f"no card with id {card_id}")

    # ===== Serialization =====

    # Convert to a JSON-ready dict. The board owns its own shape so the store
    # stays a pure file/JSON layer with no knowledge of board internals.
    def to_dict(self) -> dict:
        return {
            "next_id": self.next_id,
            "columns": {
                name: [card.to_dict() for card in cards]
                for name, cards in self.columns.items()
            },
            "archive": self.archive,
        }

    # Rebuild a board from a persisted dict. Missing columns are backfilled empty
    # so a partial or hand-edited file still produces a complete, usable board.
    @classmethod
    def from_dict(cls, data: dict) -> "Board":
        raw_columns = data.get("columns", {})
        columns = {
            name: [Card.from_dict(c) for c in raw_columns.get(name, [])]
            for name in COLUMNS
        }
        # `.get` so a pre-archive or hand-edited file loads with an empty archive.
        return cls(
            next_id=data.get("next_id", 1),
            columns=columns,
            archive=data.get("archive", []),
        )


# ===== Queries =====


# Return a copy of `columns` keeping only cards whose label equals `label`. Pure and
# non-mutating; every column key is preserved (possibly empty) so callers still get the
# full three-column shape, just narrowed. A read-only query over the board's own data —
# kept here as a section, not its own file: it is one small concern, used in one place.
def filter_by_label(
    columns: dict[str, list[Card]], label: str
) -> dict[str, list[Card]]:
    return {
        name: [card for card in cards if card.label == label]
        for name, cards in columns.items()
    }
