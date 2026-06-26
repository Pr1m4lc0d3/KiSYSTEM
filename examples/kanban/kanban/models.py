"""The Card record: the single unit of work tracked on the board.

One responsibility: define what a card *is* and how it converts to/from the
plain dicts used for JSON persistence. It holds no board rules and does no I/O.
"""

from dataclasses import dataclass
from datetime import datetime, timezone

# ===== Timestamp =====


# The one place a "now" stamp is minted: UTC, ISO-8601 to the second. Shared so
# creation (Card.new) and deletion (Board.remove) stamp time identically instead
# of each re-deriving the format.
def now_stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ===== Card =====


@dataclass
class Card:
    """A single board card: an auto-assigned id, a title, an optional label,
    and the UTC timestamp it was created. Plain data — no behaviour beyond
    construction and (de)serialization."""

    id: int
    title: str
    label: str | None
    created: str

    # Build a fresh card, stamping creation time at the moment of the call.
    # Kept as a classmethod so the timestamp is owned here, not by callers.
    @classmethod
    def new(cls, card_id: int, title: str, label: str | None = None) -> "Card":
        return cls(id=card_id, title=title, label=label, created=now_stamp())

    # Convert to a JSON-ready dict. Field names mirror the dataclass so the
    # persisted shape stays an obvious mirror of the in-memory shape.
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "label": self.label,
            "created": self.created,
        }

    # Rebuild a card from a persisted dict. `.get` on optional/legacy fields
    # so an older or hand-edited file missing them still loads instead of crashing.
    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(
            id=data["id"],
            title=data["title"],
            label=data.get("label"),
            created=data.get("created", ""),
        )
