---
name: tools-containers
description: >
  Inspect container image content straight from the registry with crane and
  skopeo, without pulling or running the image. Triggers when running crane or
  skopeo, or when asked: "what is in this image", "list files in the image",
  "read a file from an image", "image labels", "entrypoint", "env", "which user
  does it run as", "which architectures", "image digest", "list tags",
  "compare two images", "which layer added this file", "image size", operator
  bundle or catalog image contents, image signatures, attestations or SBOMs.
  Not for running containers or toolchains (use tools-podman), testcontainers
  (use dev-testcontainers), or workloads on a cluster (use tools-kubectl).
user-invocable: false
---

# Container image inspection (crane / skopeo)

Answer questions about an image from the registry. Never `podman pull` + `podman run` to look inside: that executes the image's code and downloads every layer for a question a manifest or one stream can answer.

All examples assume:

```bash
set -o pipefail            # a failing crane or tar must not look like empty output
IMG=quay.io/org/name:tag   # write "${IMG}" with braces: in zsh "$IMG:latest" applies the :l modifier
REPO=${IMG%@*}; REPO=${REPO%:*}   # no tag or digest; crane blob needs REPO@sha256:...
P=linux/amd64              # platform under inspection, always explicit
```

## Tool choice

| Need | Use | Why |
|------|-----|-----|
| Manifest, config, digest, tags, filesystem, one layer | `crane` | Streams to stdout, addresses single blobs, no policy or storage setup |
| Image in local podman storage, an OCI layout, a `docker save` archive | `skopeo` with `containers-storage:`, `oci:`, `docker-archive:` | crane only reads registries |
| A local copy to inspect many times | `skopeo copy` to `oci:.context/tmp/<name>` | One download, then offline |

## Intent dispatch

| Need | Command |
|------|---------|
| Platforms of a tag | `crane manifest "${IMG}" \| jq -r '.manifests[]?.platform \| "\(.os)/\(.architecture)"'` (no output: single-platform image) |
| Digest of the tag (index) | `crane digest "${IMG}"` |
| Digest of one platform | `crane digest --platform $P "${IMG}"` |
| Entrypoint, env, user, labels | `crane config --platform $P "${IMG}" \| jq '.config \| {Entrypoint,Cmd,Env,User,WorkingDir,Labels}'` |
| One label | `crane config --platform $P "${IMG}" \| jq -r '.config.Labels["org.opencontainers.image.revision"]'` |
| Build steps | `crane config --platform $P "${IMG}" \| jq -r '.history[] \| [(.empty_layer // false), .created_by[0:120]] \| @tsv'` |
| Layers and compressed sizes | `crane manifest --platform $P "${IMG}" \| jq -r '.layers \| to_entries[] \| [.key, .value.digest[7:19], .value.size] \| @tsv'` |
| Total compressed size | `crane manifest --platform $P "${IMG}" \| jq '[.layers[].size] \| add'` |
| List files under a path | `crane export --platform $P "${IMG}" - \| tar -tvf - usr/share/licenses` |
| Find a file by name | `crane export --platform $P "${IMG}" - \| tar -tf - --wildcards '*/os-release'` |
| Read one file | `crane export --platform $P "${IMG}" - \| tar -xOf - usr/lib/os-release` |
| Extract a directory | `mkdir -p .context/tmp/img && crane export --platform $P "${IMG}" - \| tar -xf - -C .context/tmp/img manifests metadata` |
| Content of one layer | `crane blob "${REPO}@sha256:<digest>" \| tar -tzf - \| head -50` |
| Tags | `crane ls "${REPO}" \| grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' \| sort -V \| tail -5` |
| Image in podman storage | `skopeo inspect --no-tags containers-storage:"${IMG}" \| jq '{Architecture,Digest,Labels}'` |
| Local copy | `skopeo copy --override-arch amd64 --remove-signatures -q "docker://${IMG}" oci:.context/tmp/name:latest` |

## Traps

Each of these returns a plausible wrong answer rather than an error.

- **A tag is usually an index, not an image.** `crane digest` returns the index digest, `crane config` and `crane export` silently pick `linux/amd64`, and `skopeo inspect` picks the host architecture while printing the index digest next to it. Pass `--platform` (crane) or `--override-arch` (skopeo, a global flag: `skopeo --override-arch arm64 inspect ...`), and say which platform the answer is for. Never compare an index digest with a platform digest.
- **`skopeo inspect` lists every tag of the repository** unless `--no-tags` is given: 136 KB of output for an image with 1700 tags. Always pass `--no-tags`.
- **Reading a symlink prints nothing and exits 0.** `etc/os-release` is often a link to `../usr/lib/os-release`. When a file comes back empty, list it with `tar -tvf` and read the link target.
- **Paths in the export have no leading `/`.** `tar -xOf - /etc/passwd` matches nothing.
- **`crane export` is the flattened filesystem.** Files deleted by a later layer are gone from it but still shipped; they are only visible per layer with `crane blob` (see recipes). Report a secret or large file as absent only after checking the layers.
- **Layer sizes in the manifest are compressed.** They are the download size, not the size on disk.
- **`crane ls` and `tar -t` are unbounded.** Thousands of tags and tens of thousands of files are normal. Always filter, pass a path prefix, or cap with `head`/`tail`.
- **`crane ls` order is the registry's, not chronological.** Sort with `sort -V`; "latest tag" by position is wrong.
- **`skopeo copy` to `oci:` fails on signed images** with `Pushing signatures for OCI images is not supported`. Add `--remove-signatures` for a local inspection copy.
- **Extract only under `.context/tmp/`.** An image tarball can hold thousands of files and absolute symlinks; it does not belong in the working tree.

## Authentication

crane and skopeo both read `~/.docker/config.json`; skopeo first tries `${XDG_RUNTIME_DIR}/containers/auth.json`, where `podman login` writes.

`UNAUTHORIZED`, `No matching credentials were found`, or `invalid username/password` means the user has to log in. Report the registry host and stop.

- Never run `crane auth login`, `skopeo login`, or `podman login`; credentials are the user's to enter.
- Never print an auth file or the output of `crane auth get` / `crane auth token`; they contain secrets that would land in the transcript.
- Never add `--insecure`, `--tls-verify=false`, or `--insecure-policy` to get past an error unless the user asks for it for that registry.

`MANIFEST_UNKNOWN` or `name unknown` is a wrong tag or repository, not an auth problem: check the name with `crane ls`.

## Writes

Everything above is read-only. These change a registry that other people and clusters pull from, and most cannot be undone:

- `crane copy`, `tag`, `delete`, `push`, `append`, `mutate`, `rebase`, `flatten`, `index append`
- `skopeo copy` or `skopeo sync` with a `docker://` destination, `skopeo delete`

Before a write:

1. Show the user the exact command with source and destination fully resolved; give the source by digest so the approved content cannot change under a moving tag.
2. Wait for an explicit yes, then run exactly that. One confirmation covers one command.

`skopeo copy` into a local `oci:` or `dir:` path under `.context/tmp/` is a read and needs no confirmation.

## Anti-patterns

| Do not | Why | Do instead |
|--------|-----|------------|
| `podman pull` + `podman run IMG ls /` | Runs untrusted code, pulls all layers, fails on distroless images with no shell | `crane export ... \| tar -tvf - <path>` |
| `crane pull IMG img.tar` to read one file | Writes the whole image to disk | `crane export ... \| tar -xOf - <path>` |
| `skopeo inspect docker://IMG` | Dumps every tag | `skopeo inspect --no-tags` or `crane config` |
| `tar -tvf -` with no path | Tens of thousands of lines | Path prefix, `--wildcards`, or `head` |
| Any command on a multi-arch tag without `--platform` | Answer silently applies to one architecture | `--platform $P` and state it |
| `crane manifest IMG` read as text | Index and image manifests look alike | `jq` on `.mediaType`, `.manifests`, `.layers` |
| A `for` loop of `crane config` per tag | N registry round trips | Narrow the tag list first, then inspect the few that matter |
| `podman save \| tar` to inspect a local image | Legacy layout, hashed directory names | `skopeo inspect containers-storage:IMG`, or copy to `oci:` |

## References

Read on demand:

- [references/recipes.md](references/recipes.md) — verified multi-step investigations: which layer added or deleted a path, mapping layers to build steps, diffing two images, source commit from labels, operator bundle and catalog images, signatures / attestations / SBOMs, working from a local OCI layout.
