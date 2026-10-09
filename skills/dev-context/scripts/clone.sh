#!/usr/bin/env bash
set -euo pipefail

# Clone or update a git repo into .context/repos/<org>/<repo>@<branch>,
# or a GitHub pull request into .context/repos/<org>/<repo>@pr-<number>.
# Uses git only — no gh CLI dependency.
#
# Usage: clone.sh --repo <owner/repo | url> [--branch <ref>] [--output <dir>]
#        clone.sh --pr <url | owner/repo#number> [--output <dir>]
#        clone.sh --repo <owner/repo | url> --pr <number> [--output <dir>]
# Output: prints the clone path to stdout

usage() {
    echo "Usage: clone.sh --repo <owner/repo | url> [--branch <ref>] [--output <dir>]" >&2
    echo "       clone.sh --pr <url | owner/repo#number> [--output <dir>]" >&2
    echo "       clone.sh --repo <owner/repo | url> --pr <number> [--output <dir>]" >&2
    exit 1
}

die() {
    echo "$1" >&2
    exit 1
}

BRANCH=""
OUTPUT=""
SLUG=""
PR=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo|-r)   SLUG="${2:?--repo requires a value}"; shift 2 ;;
        --branch|-b) BRANCH="${2:?--branch requires a value}"; shift 2 ;;
        --pr|-p)     PR="${2:?--pr requires a value}"; shift 2 ;;
        --output|-o) OUTPUT="${2:?--output requires a value}"; shift 2 ;;
        *)           usage ;;
    esac
done

if [[ -n "${PR}" ]]; then
    [[ -n "${BRANCH}" ]] && die "--pr and --branch are mutually exclusive"

    case "${PR}" in
        */pull/*)
            # https://host/org/repo/pull/123[/files][#fragment]
            SLUG="${PR%%/pull/*}"
            PR="${PR#*/pull/}"
            PR="${PR%%[/?#]*}"
            ;;
        *\#*)
            # org/repo#123
            SLUG="${PR%%#*}"
            PR="${PR##*#}"
            ;;
    esac

    [[ "${PR}" =~ ^[0-9]+$ ]] || die "invalid pull request number '${PR}'"
fi

[[ -z "${SLUG}" ]] && usage

[[ "${SLUG}" == */pull/* ]] && die "'${SLUG}' is a pull request URL, use --pr"

SLUG="${SLUG%/}"
SLUG="${SLUG%.git}"

if [[ "${SLUG}" == *://* || "${SLUG}" == git@* ]]; then
    URL="${SLUG}.git"
    # https://host/org/repo and git@host:org/repo both end in <org>/<repo>
    REPO_PATH="${SLUG#*://}"
    REPO_PATH="${REPO_PATH#git@}"
    REPO_PATH="${REPO_PATH/://}"
else
    URL="https://github.com/${SLUG}.git"
    REPO_PATH="${SLUG}"
fi

REPO="${REPO_PATH##*/}"
ORG="${REPO_PATH%/*}"
ORG="${ORG##*/}"

if [[ -z "${ORG}" || -z "${REPO}" || "${ORG}" == "${REPO_PATH}" ]]; then
    echo "cannot derive <org>/<repo> from '${SLUG}'" >&2
    exit 1
fi

if [[ -n "${PR}" ]]; then
    REF="pr-${PR}"
else
    if [[ -z "${BRANCH}" ]]; then
        BRANCH=$(git ls-remote --symref "${URL}" HEAD | awk '/^ref:/{sub(/.*refs\/heads\//, ""); print $1}')
    fi
    REF="${BRANCH}"
fi

if [[ -n "${OUTPUT}" ]]; then
    CLONE_DIR="${OUTPUT}"
else
    CONTEXT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.context/repos"
    # a ref like feature/x must not turn into a nested directory
    CLONE_DIR="${CONTEXT_DIR}/${ORG}/${REPO}@${REF//\//-}"
fi

mkdir -p "$(dirname "${CLONE_DIR}")"

if [[ -n "${PR}" ]]; then
    # refs/pull/<n>/head lives on the upstream repo, so it works even when the
    # head fork or branch is gone. PR heads get force-pushed: always re-fetch.
    if [[ ! -d "${CLONE_DIR}/.git" ]]; then
        git init -q "${CLONE_DIR}"
        git -C "${CLONE_DIR}" remote add origin "${URL}"
    fi
    git -C "${CLONE_DIR}" fetch -q --depth 1 origin "+refs/pull/${PR}/head:refs/remotes/origin/${REF}"
    git -C "${CLONE_DIR}" checkout -q -B "${REF}" "refs/remotes/origin/${REF}"
elif [[ -d "${CLONE_DIR}" ]]; then
    git -C "${CLONE_DIR}" pull --ff-only -q
else
    git clone -q --depth 1 --single-branch --branch "${BRANCH}" "${URL}" "${CLONE_DIR}"
fi

echo "${CLONE_DIR}"
