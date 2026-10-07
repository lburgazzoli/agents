"""Download the artifacts of one openshift-ci run with gcloud storage.

Assumes gcloud is already authenticated.

Tiers:
  triage (default)  job metadata, logs and junit of every step except the
                    gather-* steps. A few MB.
  gather            triage + the gather-* steps (cluster state, must-gather)
                    without archives such as the Prometheus dump. Hundreds
                    of MB, thousands of files, about a minute per step.
  all               everything. Can exceed 1 GB.

--step <name> fetches the named step(s) on top of the tier, e.g.
--step gather-extra.

Output: prints the local run directory to stdout. Re-running only transfers
what is missing.
"""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .common import add_command, die, git_toplevel, gs_url, info, run

ARCHIVES = r".*\.(tar|tgz|tar\.gz|tar\.xz|zip)$"
PARALLEL = 4


def register(subcommands):
    cmd = add_command(subcommands, "fetch", __doc__, execute)
    cmd.add_argument("url", help="gs:// or Prow URL of the run")
    cmd.add_argument("--tier", choices=["triage", "gather", "all"], default="triage")
    cmd.add_argument("--step", action="append", default=[], help="also fetch this step; repeatable")
    cmd.add_argument("--output", "-o", help="destination directory")


def default_output(src):
    rel = src.removeprefix("gs://").split("/", 1)[1].removeprefix("pr-logs/pull/")
    return Path(git_toplevel() or os.getcwd()) / ".context" / "openshift-ci" / rel


def sync(src, output, rel, *flags):
    """rsync <src>/<rel> into <output>/<rel>; non-recursive unless flagged."""
    dest = output / rel
    dest.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        ["gcloud", "storage", "rsync", f"{src}/{rel}".rstrip("/"), str(dest), *flags],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        die(f"download of {src}/{rel} failed:\n" + "\n".join(proc.stderr.splitlines()[-20:]))


def ls(pattern):
    return (run("gcloud", "storage", "ls", pattern) or "").split()


def targets(src, tier, steps):
    """The artifacts/ subdirectories to fetch recursively.

    artifacts/<dir>/ either holds the steps of a test (each with its own
    finished.json) or is a small ci-operator folder (build-logs, release).
    """
    prefix = f"{src}/artifacts/"
    step_dirs = [u.removeprefix(prefix).removesuffix("/finished.json") for u in ls(f"{prefix}*/*/finished.json")]
    top_dirs = [u.removeprefix(prefix).rstrip("/") for u in ls(prefix) if u.endswith("/")]

    def wanted(step):
        name = step.rsplit("/", 1)[-1]
        return name in steps or not (name.startswith("gather-") and tier == "triage")

    result = []
    for top in top_dirs:
        own_steps = [s for s in step_dirs if s.split("/", 1)[0] == top]
        if own_steps:
            result += [f"artifacts/{s}" for s in own_steps if wanted(s)]
        else:
            result.append(f"artifacts/{top}")
    return result


def disk_usage(path):
    return (run("du", "-sh", str(path)) or "?").split()[0]


def execute(args):
    src = gs_url(args.url)
    output = Path(args.output) if args.output else default_output(src)
    output.mkdir(parents=True, exist_ok=True)

    if args.tier == "all":
        size = (run("gcloud", "storage", "du", "-s", "-r", src) or "?").split()[0]
        info(f"size of the run: {size}")
        sync(src, output, "", "--recursive")
        print(output)
        return 0

    # Top-level files of the run and of artifacts/ (non-recursive).
    sync(src, output, "")
    sync(src, output, "artifacts")

    with ThreadPoolExecutor(max_workers=PARALLEL) as pool:
        jobs = [
            pool.submit(sync, src, output, rel, "--recursive", "--exclude", ARCHIVES)
            for rel in targets(src, args.tier, args.step)
        ]
        for job in jobs:
            job.result()

    info(f"{disk_usage(output)} in {output}")
    print(output)
    return 0
