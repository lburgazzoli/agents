#!/usr/bin/env bash
set -euo pipefail

# Clone or update a GitHub repo into .context/repos/<repo>@<branch>.
# Uses git only — no gh CLI dependency.
#
# Usage: clone.sh --repo <owner/repo> [--branch <ref>] [--output <dir>]
# Output: prints the absolute clone path to stdout

usage() {
    echo "Usage: clone.sh --repo <owner/repo> [--branch <ref>] [--output <dir>]" >&2
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

if [[ "${SLUG}" == https://* || "${SLUG}" == git@* ]]; then
    URL="${SLUG%.git}.git"
    REPO="$(basename "${SLUG}" .git)"
else
    URL="https://github.com/${SLUG}.git"
    REPO="${SLUG##*/}"
fi

if [[ -z "${BRANCH}" ]]; then
    BRANCH=$(git ls-remote --symref "${URL}" HEAD | awk '/^ref:/{sub(/.*refs\/heads\//, ""); print $1}')
fi

if [[ -n "${OUTPUT}" ]]; then
    CLONE_DIR="${OUTPUT}"
else
    CONTEXT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.context/repos"
    CLONE_DIR="${CONTEXT_DIR}/${REPO}@${BRANCH}"
fi

mkdir -p "$(dirname "${CLONE_DIR}")"

if [[ -d "${CLONE_DIR}" ]]; then
    git -C "${CLONE_DIR}" pull --ff-only -q
else
    git clone --depth 1 --single-branch --branch "${BRANCH}" "${URL}" "${CLONE_DIR}"
fi

echo "${CLONE_DIR}"
