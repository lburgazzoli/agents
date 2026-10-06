#!/usr/bin/env bash
set -euo pipefail

# Clone or update a git repo into .context/repos/<org>/<repo>@<branch>.
# Uses git only — no gh CLI dependency.
#
# Usage: clone.sh --repo <owner/repo | url> [--branch <ref>] [--output <dir>]
# Output: prints the clone path to stdout

usage() {
    echo "Usage: clone.sh --repo <owner/repo | url> [--branch <ref>] [--output <dir>]" >&2
    exit 1
}

BRANCH=""
OUTPUT=""
SLUG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --repo|-r)   SLUG="${2:?--repo requires a value}"; shift 2 ;;
        --branch|-b) BRANCH="${2:?--branch requires a value}"; shift 2 ;;
        --output|-o) OUTPUT="${2:?--output requires a value}"; shift 2 ;;
        *)           usage ;;
    esac
done

[[ -z "${SLUG}" ]] && usage

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

if [[ -z "${BRANCH}" ]]; then
    BRANCH=$(git ls-remote --symref "${URL}" HEAD | awk '/^ref:/{sub(/.*refs\/heads\//, ""); print $1}')
fi

if [[ -n "${OUTPUT}" ]]; then
    CLONE_DIR="${OUTPUT}"
else
    CONTEXT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.context/repos"
    CLONE_DIR="${CONTEXT_DIR}/${ORG}/${REPO}@${BRANCH}"
fi

mkdir -p "$(dirname "${CLONE_DIR}")"

if [[ -d "${CLONE_DIR}" ]]; then
    git -C "${CLONE_DIR}" pull --ff-only -q
else
    git clone -q --depth 1 --single-branch --branch "${BRANCH}" "${URL}" "${CLONE_DIR}"
fi

echo "${CLONE_DIR}"
