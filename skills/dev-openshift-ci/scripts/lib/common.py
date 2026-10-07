"""Helpers shared by the subcommands."""

import argparse
import json
import subprocess
import sys

PROW = "https://prow.ci.openshift.org/view/gs/"


def die(message):
    print(f"openshift-ci: {message}", file=sys.stderr)
    sys.exit(1)


def info(message):
    print(f"openshift-ci: {message}", file=sys.stderr)


def run(*cmd):
    """Run a command; return its stdout, or None when it fails."""
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def gs_url(url):
    """A Prow or gs:// URL of a run as a gs:// URL without trailing slash."""
    url = url.rstrip("/")
    if url.startswith(PROW):
        return "gs://" + url.removeprefix(PROW)
    if url.startswith("gs://"):
        return url
    die(f"expected a gs:// or Prow URL, got '{url}'")


def prow_url(url):
    return PROW + gs_url(url).removeprefix("gs://")


def git_toplevel():
    return run("git", "rev-parse", "--show-toplevel")


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def add_command(subcommands, name, doc, run_func):
    """Add a subcommand whose help is the module docstring."""
    summary, _, details = doc.strip().partition("\n")
    parser = subcommands.add_parser(
        name,
        help=summary,
        description=summary,
        epilog=details.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.set_defaults(run=run_func)
    return parser
