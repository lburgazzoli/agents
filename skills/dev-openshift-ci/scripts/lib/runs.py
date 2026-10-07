"""Resolve the openshift-ci runs to analyze for a pull request.

Only openshift-ci[bot] is a source: its test report comment and its
ci/prow/* commit statuses. Other bots, human comments and other checks are
ignored.

target: 4137 | '#4137' | owner/repo#4137 | PR URL | comment URL
        (...#issuecomment-<id>) | Prow URL | gs:// URL
        With no target, the PR of the current branch is used.
        A bare number takes the repo from the current git checkout.

Output: TSV on stdout, newest first:
  context  state  build_id  created_at  gs_url  prow_url

Exit codes: 0 resolved, 1 error, 2 cannot determine which run to use
(candidates are printed; show them to the user and ask).
"""

import json
import re
from dataclasses import dataclass

from .common import PROW, add_command, die, gs_url, info, prow_url, run

BOT = "openshift-ci[bot]"
REPORT_MARKER = "<!-- test report -->"

PR_URL = re.compile(r"^https://github\.com/([^/]+/[^/]+)/pull/(\d+)(?:.*#issuecomment-(\d+))?")
REPO_PR = re.compile(r"^([^/#\s]+/[^/#\s]+)#(\d+)$")
BARE_PR = re.compile(r"^#?(\d+)$")
PROW_LINK = re.compile(r"\]\((" + re.escape(PROW) + r"[^)]+)\)")


def register(subcommands):
    cmd = add_command(subcommands, "runs", __doc__, execute)
    cmd.add_argument("target", nargs="?", default="")
    cmd.add_argument("--repo", "-R", default="", help="owner/repo, overrides the one derived from the target")
    cmd.add_argument("--list", action="store_true", help="print the candidates without choosing")
    cmd.add_argument("--build", default="", help="pick the run with this build id")
    cmd.add_argument("--job", default="", help="only jobs whose context contains this")
    cmd.add_argument("--sha", default="", help="look at this commit instead of the PR head")


@dataclass
class Run:
    context: str
    state: str
    created_at: str
    prow_url: str
    sha: str = ""

    @property
    def build_id(self):
        return self.prow_url.rstrip("/").rsplit("/", 1)[-1]

    def tsv(self):
        return "\t".join([self.context, self.state, self.build_id, self.created_at, gs_url(self.prow_url), self.prow_url.rstrip("/")])


def gh_json(*args):
    out = run("gh", *args)
    return None if out is None else json.loads(out)


def gh_pages(path):
    """All pages of a REST list endpoint, flattened."""
    pages = gh_json("api", "--paginate", "--slurp", path)
    if pages is None:
        die(f"gh api {path} failed")
    return [item for page in pages for item in page]


def require_git_repo():
    if run("git", "rev-parse", "--is-inside-work-tree") is None:
        die("not inside a git repository: pass --repo <owner/repo>, owner/repo#<n>, or a PR URL")


def checkout_repo(pr):
    """The GitHub repo of the git checkout the caller is in.

    gh follows its own base-repo resolution (set-default, then upstream
    before origin), so a fork checkout resolves to the repo where the PR and
    its CI live.
    """
    require_git_repo()

    repo_info = gh_json("repo", "view", "--json", "nameWithOwner,parent")
    if repo_info is None:
        die("cannot determine the GitHub repo of this checkout: pass --repo <owner/repo>")

    repo = repo_info["nameWithOwner"]
    parent = repo_info.get("parent")
    if parent and run("gh", "pr", "view", pr, "-R", repo, "--json", "number") is None:
        repo = f"{parent['owner']['login']}/{parent['name']}"
    return repo


def parse_target(target, repo):
    """Return (repo, pr, comment_id) from what the user gave."""
    if not target:
        if repo:
            die("no PR number given")
        require_git_repo()
        target = run("gh", "pr", "view", "--json", "url", "--jq", ".url")
        if not target:
            die("no pull request found for the current branch: pass a PR number")

    if m := PR_URL.match(target):
        return repo or m[1], m[2], m[3]
    if m := REPO_PR.match(target):
        return repo or m[1], m[2], None
    if m := BARE_PR.match(target):
        return repo or checkout_repo(m[1]), m[1], None

    die(f"cannot parse a PR from '{target}'")


def is_report(comment):
    return comment["user"]["login"] == BOT and REPORT_MARKER in comment["body"]


def comment_runs(comment):
    """Rows of a test report: name | commit | [link](prow url) | required | rerun."""
    runs = []
    for line in comment["body"].splitlines():
        link = PROW_LINK.search(line)
        if not link:
            continue
        cells = [c.strip() for c in line.split("|")]
        runs.append(Run(context=cells[0], state="failure", created_at=comment["updated_at"], prow_url=link[1], sha=cells[1]))
    return runs


def status_runs(repo, sha):
    """One Run per ci/prow run of the commit, with its newest state."""
    latest = {}
    for status in gh_pages(f"repos/{repo}/commits/{sha}/statuses"):
        url = status.get("target_url") or ""
        if (status["creator"] or {}).get("login") != BOT:
            continue
        if not status["context"].startswith("ci/prow/") or not url.startswith(PROW):
            continue
        if url not in latest or status["created_at"] > latest[url]["created_at"]:
            latest[url] = status
    runs = [Run(s["context"], s["state"], s["created_at"], s["target_url"]) for s in latest.values()]
    return sorted(runs, key=lambda r: r.created_at, reverse=True)


def emit(runs, job):
    rows = [r for r in runs if not job or job in r.context]
    if not rows:
        die("no run matches" + (f" --job {job}" if job else ""))
    for r in rows:
        print(r.tsv())


def print_candidates(repo, pr, sha, comments, runs, job):
    print(f"# openshift-ci test report comments on {repo}#{pr}: comment_url  updated_at  commit  failed_jobs")
    for c in comments:
        rows = comment_runs(c)
        shas = ",".join(sorted({r.sha for r in rows}))
        print("\t".join([c["html_url"], c["updated_at"], shas, ",".join(r.context for r in rows)]))

    print(f"# ci/prow runs for {sha}: context  state  build_id  created_at  gs_url  prow_url")
    for r in runs:
        if not job or job in r.context:
            print(r.tsv())


def execute(args):
    # A run addressed directly needs no GitHub lookup.
    if args.target.startswith((PROW, "gs://")):
        url = prow_url(args.target)
        print(Run(url.split("/")[-2], "unknown", "-", url).tsv())
        return 0

    repo, pr, comment_id = parse_target(args.target, args.repo)

    head = run("gh", "pr", "view", pr, "-R", repo, "--json", "headRefOid", "--jq", ".headRefOid")
    if not head:
        die(f"pull request {repo}#{pr} not found")
    sha = args.sha or head
    info(f"{repo}#{pr} @ {sha}")

    # An explicit comment: it must be an openshift-ci test report.
    if comment_id:
        comment = gh_json("api", f"repos/{repo}/issues/comments/{comment_id}")
        if comment is None:
            die(f"comment {comment_id} not found in {repo}")
        if not is_report(comment):
            die(f"not an openshift-ci test report comment: {args.target}")
        emit(comment_runs(comment), args.job)
        return 0

    runs = status_runs(repo, sha)
    comments = [c for c in gh_pages(f"repos/{repo}/issues/{pr}/comments") if is_report(c)]
    comments.sort(key=lambda c: c["created_at"], reverse=True)

    if args.list:
        print_candidates(repo, pr, sha, comments, runs, args.job)
        return 0

    if args.build:
        known = {r.prow_url.rstrip("/"): r for c in comments for r in comment_runs(c)}
        known.update({r.prow_url.rstrip("/"): r for r in runs})
        match = [r for r in known.values() if r.build_id == args.build]
        if not match:
            die(f"build {args.build} is not an openshift-ci run of {repo}#{pr} @ {sha}: pass its Prow URL or --sha")
        emit(match, args.job)
        return 0

    # Default: the latest test report comment, when it describes this commit.
    reason = None
    latest = comment_runs(comments[0]) if comments else []
    if not comments:
        reason = "no openshift-ci test report comment on the PR"
    elif not latest:
        reason = "the latest test report comment lists no runs"
    elif any(r.sha != sha for r in latest):
        reason = f"the latest test report comment is for another commit than {sha}"

    if reason:
        info(f"cannot determine the run to analyze: {reason}")
        info("show the candidates below and ask which one to use, then rerun with a comment URL or --build <id>")
        print_candidates(repo, pr, sha, comments, runs, args.job)
        return 2

    emit(latest, args.job)
    return 0
