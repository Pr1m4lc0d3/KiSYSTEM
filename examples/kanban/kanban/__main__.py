"""Module entry point so `python -m kanban ...` runs the CLI.

One responsibility: hand control to cli.main and translate its return value into
the process exit code.
"""

import sys

from kanban.cli import main

if __name__ == "__main__":
    sys.exit(main())
