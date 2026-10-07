#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Retrieve and analyze OpenShift CI (Prow) runs of a pull request.

Each subcommand lives in its own module under lib/ and registers itself
here, the way cobra commands are added to a root command.
"""

import argparse
import sys

# Keep the skill directory free of __pycache__.
sys.dont_write_bytecode = True

from lib import fetch, junit, runs, summary

COMMANDS = [runs, fetch, summary, junit]


def main():
    root = argparse.ArgumentParser(
        prog="main.py",
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subcommands = root.add_subparsers(title="commands", dest="command", metavar="<command>", required=True)

    for command in COMMANDS:
        command.register(subcommands)

    args = root.parse_args()
    sys.exit(args.run(args) or 0)


if __name__ == "__main__":
    main()
