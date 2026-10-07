"""Print the failed test cases of junit XML reports as JSON Lines.

Each line: {"file", "suite", "classname", "name", "time", "message", "output"}

By default only leaf failures are printed: a failed test is dropped when a
failed test named "<name>/..." exists in the same file, because a Go parent
test fails whenever one of its subtests does and repeats their output.
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from .common import add_command, info


def register(subcommands):
    cmd = add_command(subcommands, "junit", __doc__, execute)
    cmd.add_argument("paths", nargs="+", help="junit XML files, or directories searched for junit*.xml")
    cmd.add_argument("--all-failed", action="store_true", help="include parent tests of failed subtests")
    cmd.add_argument("--max-chars", type=int, default=2000, help="keep the last N chars of each output; 0 keeps all (default: 2000)")
    cmd.add_argument("--name", help="only tests whose name matches this regex")


def reports(paths):
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            yield from sorted(path.rglob("junit*.xml"))
        else:
            yield path


def failed_cases(path):
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as err:
        info(f"skipping {path}: {err}")
        return

    # The root is either <testsuites> or a bare <testsuite>.
    for suite in root.iter("testsuite"):
        for case in suite.findall("testcase"):
            problem = case.find("failure")
            if problem is None:
                problem = case.find("error")
            if problem is None:
                continue
            yield {
                "file": str(path),
                "suite": suite.get("name", ""),
                "classname": case.get("classname", ""),
                "name": case.get("name", ""),
                "time": float(case.get("time") or 0),
                "message": problem.get("message", ""),
                "output": problem.text or "",
            }


def leaves(cases):
    parents = set()
    for case in cases:
        parts = case["name"].split("/")
        for i in range(1, len(parts)):
            parents.add("/".join(parts[:i]))
    return [c for c in cases if c["name"] not in parents]


def execute(args):
    pattern = re.compile(args.name) if args.name else None

    for path in reports(args.paths):
        cases = list(failed_cases(path))
        if not args.all_failed:
            cases = leaves(cases)
        for case in cases:
            if pattern and not pattern.search(case["name"]):
                continue
            # Go prints the assertion last, so the tail is the useful part.
            if args.max_chars and len(case["output"]) > args.max_chars:
                case["output"] = "[...]" + case["output"][-args.max_chars:]
            print(json.dumps(case, ensure_ascii=False))
    return 0
