"""Summarize a downloaded openshift-ci run.

Prints the job, its result, the failed ci-operator steps and substeps, each
step's result with its path, and the junit reports with their failure
counts.

run_dir is the path printed by the fetch command.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

from .common import add_command, die, info, load_json


def register(subcommands):
    cmd = add_command(subcommands, "summary", __doc__, execute)
    cmd.add_argument("run_dir")


def row(*cells):
    print("\t".join(str(c) for c in cells))


def seconds(nanoseconds):
    return f"{int((nanoseconds or 0) / 1e9)}s"


def print_job(run_dir):
    print("## Job")

    prowjob = run_dir / "prowjob.json"
    if prowjob.is_file():
        job = load_json(prowjob)
        spec, status = job["spec"], job["status"]
        refs = spec.get("refs") or {}
        row("job", spec["job"])
        row("type", spec["type"])
        row("repo", f"{refs.get('org', '')}/{refs.get('repo', '')}@{refs.get('base_ref', '')}")
        for pull in refs.get("pulls") or []:
            row("pull", f"#{pull['number']} {pull['sha']} ({pull['author']})")
        row("state", status["state"])
        row("started", status.get("startTime", "-"))
        row("completed", status.get("completionTime", "-"))
        row("url", status.get("url", "-"))

    finished = run_dir / "finished.json"
    if finished.is_file():
        row("result", load_json(finished)["result"])
    else:
        row("result", "not finished (no finished.json): the run is still pending or was not fully fetched")


def print_failed_steps(run_dir):
    graph = run_dir / "artifacts" / "ci-operator-step-graph.json"
    try:
        steps = load_json(graph)
        if not isinstance(steps, list):
            raise ValueError("expected a list of steps")

        # Prepare rows before printing so an invalid graph cannot leave a
        # partial failed-step summary. Prow may replace this file with text.
        rows = []
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError("expected each step to be an object")
            if not step.get("failed"):
                continue
            rows.append(("", step["name"], seconds(step.get("duration"))))
            substeps = step.get("substeps") or []
            if not isinstance(substeps, list):
                raise ValueError("expected substeps to be a list")
            for sub in substeps:
                if not isinstance(sub, dict):
                    raise ValueError("expected each substep to be an object")
                if sub.get("failed"):
                    rows.append(("  ", sub["name"], seconds(sub.get("duration"))))
    except (OSError, UnicodeError, ValueError, TypeError, KeyError) as err:
        info(f"warning: step graph unavailable ({graph}): {err}; "
             "continuing with step results and JUnit reports")
        return

    print("\n## Failed ci-operator steps: step  duration  [substep  duration]")
    for indent, name, duration in rows:
        print(indent, end="")
        row(name, duration)


def print_steps(run_dir):
    print("\n## Steps: result  path")
    for finished in sorted((run_dir / "artifacts").glob("*/*/finished.json")):
        data = load_json(finished)
        result = data.get("result") or ("SUCCESS" if data.get("passed") else "FAILURE")
        row(result, finished.parent.relative_to(run_dir))


def root_counts(path):
    """failures and tests of the report: from <testsuites>, else its first <testsuite>."""
    try:
        for _, element in ET.iterparse(path, events=("start",)):
            if element.tag not in ("testsuites", "testsuite"):
                break
            if element.get("tests") is not None:
                return element.get("failures", "-"), element.get("tests", "-")
    except (ET.ParseError, OSError):
        pass
    return "-", "-"


def print_junit(run_dir):
    # The report's own totals; the junit command gives the real list.
    print("\n## Junit reports: failures  tests  path")
    for report in sorted(run_dir.rglob("junit*.xml")):
        failures, tests = root_counts(report)
        row(failures, tests, report.relative_to(run_dir))


def execute(args):
    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        die(f"'{run_dir}' is not a directory")

    print_job(run_dir)
    print_failed_steps(run_dir)
    print_steps(run_dir)
    print_junit(run_dir)
    return 0
