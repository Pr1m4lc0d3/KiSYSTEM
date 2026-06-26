"""Command line: parse arguments and dispatch to the board, store, and render.

One responsibility: wiring. It owns the argparse surface and the load → act →
save flow for each command. All actual rules live in board/store/render;
this file only connects them to the terminal.
"""

import argparse

from kanban.board import COLUMNS, filter_by_label
from kanban.render import render_archive, render_board
from kanban.store import load_board, save_board
from kanban.web import serve

DEFAULT_FILE = "board.json"
DEFAULT_PORT = 8000

# ===== Argument parsing =====


# Build the argparse parser: a shared --file option plus one subcommand per
# action. Kept in one function so the whole CLI surface is visible at a glance.
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kanban", description="A tiny terminal Kanban board."
    )
    parser.add_argument(
        "--file", default=DEFAULT_FILE, help="board JSON file (default: board.json)"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    add_cmd = subcommands.add_parser("add", help="add a card to todo")
    add_cmd.add_argument("title", help="card title")
    add_cmd.add_argument("--label", help="optional label")

    move_cmd = subcommands.add_parser("move", help="move a card to a column")
    move_cmd.add_argument("id", type=int, help="card id")
    move_cmd.add_argument("column", choices=COLUMNS, help="target column")

    list_cmd = subcommands.add_parser("list", help="show the board")
    list_cmd.add_argument("--label", help="show only cards with this label")

    remove_cmd = subcommands.add_parser("remove", help="delete a card")
    remove_cmd.add_argument("id", type=int, help="card id")

    # archive: list deleted cards. No args — it reads the whole archive.
    subcommands.add_parser("archive", help="list deleted cards")

    # serve: a second interface (web UI) over the same board file as the commands
    # above. --file is the shared global option; only the port is local here.
    serve_cmd = subcommands.add_parser("serve", help="serve the web UI")
    serve_cmd.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help="port (default: 8000)"
    )

    return parser


# ===== Command handlers =====
# Each handler loads the board, performs one action, persists if it changed
# state, and prints a short confirmation. They return a process exit code.


# add: create a card in todo and save.
def _do_add(args: argparse.Namespace) -> int:
    board = load_board(args.file)
    card = board.add(args.title, args.label)
    save_board(args.file, board)
    print(f"Added #{card.id} '{card.title}' to todo.")
    return 0


# move: relocate a card, reporting a clear message if the id is unknown.
def _do_move(args: argparse.Namespace) -> int:
    board = load_board(args.file)
    try:
        card = board.move(args.id, args.column)
    except KeyError as error:
        print(f"Error: {error}")
        return 1
    save_board(args.file, board)
    print(f"Moved #{card.id} '{card.title}' to {args.column}.")
    return 0


# remove: delete a card, reporting a clear message if the id is unknown.
def _do_remove(args: argparse.Namespace) -> int:
    board = load_board(args.file)
    try:
        card = board.remove(args.id)
    except KeyError as error:
        print(f"Error: {error}")
        return 1
    save_board(args.file, board)
    print(f"Removed #{card.id} '{card.title}'.")
    return 0


# list: render the board, optionally narrowed to one label. Read-only, no save.
def _do_list(args: argparse.Namespace) -> int:
    board = load_board(args.file)
    columns = board.columns
    if args.label:
        columns = filter_by_label(columns, args.label)
    print(render_board(columns))
    return 0


# archive: show the deleted-card history. Read-only — no save, like list.
def _do_archive(args: argparse.Namespace) -> int:
    board = load_board(args.file)
    print(render_archive(board.archive))
    return 0


# serve: start the web UI over the same board file. Blocks until Ctrl-C, which
# we catch so stopping the server is a clean exit, not a stack trace.
def _do_serve(args: argparse.Namespace) -> int:
    try:
        serve(args.port, args.file)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    return 0


# Maps the parsed command name to its handler, avoiding an if/elif ladder.
_HANDLERS = {
    "add": _do_add,
    "move": _do_move,
    "list": _do_list,
    "remove": _do_remove,
    "archive": _do_archive,
    "serve": _do_serve,
}


# ===== Entry =====


# Parse argv and run the matching handler. Returned int is the process exit code.
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return _HANDLERS[args.command](args)
