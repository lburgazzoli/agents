# Image investigation recipes

Verified against public images with crane 0.22 and skopeo 1.22. All assume the setup from `SKILL.md`:

```bash
set -o pipefail
IMG=quay.io/org/name:tag
REPO=${IMG%@*}; REPO=${REPO%:*}
P=linux/amd64
```

## Which layer added, changed, or deleted a path

`crane export` shows only the final filesystem. Walk the layers to see where a path came from and whether an earlier copy is still shipped:

```bash
i=0
for d in $(crane manifest --platform $P "${IMG}" | jq -r '.layers[].digest'); do
  crane blob "${REPO}@${d}" | tar -tzf - 2>/dev/null \
    | grep -E '(^|/)(prometheus\.yml|\.wh\.[^/]*)$' | sed "s|^|$i ${d:7:12}  |"
  i=$((i+1))
done
```

- A path printed for several layers was rewritten; the highest index wins.
- `dir/.wh.name` is a whiteout: that layer deletes `dir/name`. `dir/.wh..wh..opq` hides everything an earlier layer put in `dir`.
- To read the shadowed or deleted version: `crane blob "${REPO}@sha256:<digest>" | tar -xzOf - path/to/file`.
- This downloads every layer once. Check the layer sizes first and skip the base layers when the path clearly comes from the application.

## Map a layer to its build step

The config history has one entry per build instruction; entries with `empty_layer: true` (ENV, LABEL, CMD) produce no layer. Dropping them lines the rest up with the manifest's layers by index:

```bash
crane config --platform $P "${IMG}" \
  | jq -r '[.history[] | select(.empty_layer != true)] | to_entries[] | [.key, .value.created_by[0:100]] | @tsv'
```

The index matches the first column of the layer listing in `SKILL.md` and of the loop above. Images built by squashing tools report a single layer with one history entry; there is nothing to map.

## Diff two images

Start with the cheapest comparison and stop when the question is answered.

```bash
A=quay.io/org/name:v1; B=quay.io/org/name:v2

# 1. same content? identical platform digests means identical images
crane digest --platform $P "${A}"; crane digest --platform $P "${B}"

# 2. how many layers are shared (same base, same dependencies)
comm -12 <(crane manifest --platform $P "${A}" | jq -r '.layers[].digest' | sort) \
         <(crane manifest --platform $P "${B}" | jq -r '.layers[].digest' | sort) | wc -l

# 3. runtime configuration
diff <(crane config --platform $P "${A}" | jq -S '.config') \
     <(crane config --platform $P "${B}" | jq -S '.config')

# 4. files added, removed, or resized
diff <(crane export --platform $P "${A}" - | tar -tvf - | awk '{print $3, $6}' | sort -k2) \
     <(crane export --platform $P "${B}" - | tar -tvf - | awk '{print $3, $6}' | sort -k2) | head -60
```

Step 4 compares size and path only, so a same-size content change is not reported; rebuilt binaries usually differ in size. To compare one file's content, read it from both images with `tar -xOf -` and diff those.

## Source commit and build provenance from labels

```bash
crane config --platform $P "${IMG}" | jq -r '
  .config.Labels | to_entries[]
  | select(.key | test("^org\\.opencontainers\\.image\\.|^vcs-|^io\\.openshift\\.|^(name|version|release|build-date)$"))
  | [.key, .value[0:100]] | @tsv'
```

`org.opencontainers.image.revision` or `vcs-ref` is the commit, `org.opencontainers.image.source` or `url` the repository. Labels are set by whoever built the image and are not verified; for a trustworthy answer use the attestation below.

## Operator bundle images

A bundle is a small single-platform image holding only YAML. Its labels describe it without downloading anything:

```bash
crane config "${IMG}" | jq -r '
  .config.Labels | to_entries[]
  | select(.key | startswith("operators.operatorframework.io.bundle")) | [.key, .value] | @tsv'
```

```bash
# what it ships
crane export "${IMG}" - | tar -tf - manifests metadata

# the ClusterServiceVersion
crane export "${IMG}" - | tar -xOf - --wildcards 'manifests/*clusterserviceversion.yaml' > .context/tmp/csv.yaml

# everything, for grep or yq
mkdir -p .context/tmp/bundle && crane export "${IMG}" - | tar -xf - -C .context/tmp/bundle manifests metadata
```

Write the CSV to a file rather than the terminal: it embeds CRD descriptors and a base64 icon and often runs to thousands of lines.

## File-based catalog images

The label `operators.operatorframework.io.index.configs.v1` names the catalog directory (normally `/configs`). Catalogs are hundreds of megabytes, so every command below streams the whole image; ask for one package rather than the lot.

```bash
# packages in the catalog
crane export --platform $P "${IMG}" - | tar -tf - configs | awk -F/ 'NF==2 && $2!="" {print $2}' | sort -u

# one package
mkdir -p .context/tmp/catalog
crane export --platform $P "${IMG}" - | tar -xf - -C .context/tmp/catalog configs/cert-manager
```

Several questions about the same catalog: make one local copy first (see the last section) instead of streaming it each time.

## Signatures, attestations, SBOMs

cosign stores them as tags in the same repository, named after the digest they describe:

```bash
D=$(crane digest --platform $P "${IMG}")
T="sha256-${D#sha256:}"
crane ls "${REPO}" | grep "^${T}"          # .sig  .att  .sbom
```

If nothing matches, repeat with the index digest (`crane digest "${IMG}"`): some pipelines sign the index, some each platform, some both.

```bash
# SBOM: check the size, then save it; it is large
crane manifest "${REPO}:${T}.sbom" | jq -c '.layers[] | {mediaType, size}'
crane blob "${REPO}@$(crane manifest "${REPO}:${T}.sbom" | jq -r '.layers[0].digest')" > .context/tmp/sbom.json

# attestation: a DSSE envelope with a base64 in-toto statement
crane blob "${REPO}@$(crane manifest "${REPO}:${T}.att" | jq -r '.layers[0].digest')" \
  | jq -r '.payload' | base64 -d | jq '{predicateType, builder: .predicate.builder, materials: .predicate.materials[0:5]}'
```

Finding these tags shows that a signature exists, not that it is valid. Verification needs `cosign verify` with the expected key or identity; say so rather than reporting the image as "signed and verified".

## Local images and repeated inspection

```bash
# an image built or pulled with podman, no registry involved
skopeo inspect --no-tags containers-storage:"${IMG}" | jq '{Architecture, Digest, Layers: (.Layers | length)}'
skopeo inspect --config containers-storage:"${IMG}" | jq '.config'

# one download, then offline
skopeo copy --override-arch amd64 --remove-signatures -q "docker://${IMG}" oci:.context/tmp/name:latest
skopeo inspect --no-tags oci:.context/tmp/name:latest | jq '{Architecture, Layers}'
```

Inside the layout, `index.json` points at the manifest and every manifest, config, and layer is a file `blobs/sha256/<hex>`:

```bash
L=.context/tmp/name
M=$(jq -r '.manifests[0].digest[7:]' $L/index.json)
jq -r '.layers[].digest[7:]' $L/blobs/sha256/$M | while read -r d; do
  tar -tzf $L/blobs/sha256/$d | grep -E '^configs/cert-manager/' | head -5
done
```

Remove the layout from `.context/tmp/` when the investigation is done.
