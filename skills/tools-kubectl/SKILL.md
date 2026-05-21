---
name: tools-kubectl
description: kubectl/oc CLI patterns for token-efficient Kubernetes operations. Triggers when running kubectl, oc, or Kubernetes API commands.
user-invocable: false
---

# kubectl / oc Guidelines

Prefer `kubectl` for all standard Kubernetes operations. Use `oc` only for subcommands that have no kubectl equivalent (`oc login`). Always minimize output. Never dump full resources. Use jq as the only external processing tool — no python, awk, or grep on kubectl output.

## Output format decision tree

| Need | Format | Example |
|------|--------|---------|
| Existence check | `-o name --ignore-not-found` | `kubectl get pod foo -o name --ignore-not-found` |
| One field | `-o jsonpath='{.path}'` | `kubectl get pod foo -o jsonpath='{.status.phase}'` |
| 2-4 fields, tabular | `-o custom-columns=... --no-headers` | see below |
| Complex filter/sort/count | `-o json \| jq` | see jq recipes |
| What would change | `kubectl diff -f` | `kubectl diff -f manifest.yaml` |
| Wait for condition | `kubectl wait --for=...` | `kubectl wait --for=condition=Ready pod/foo --timeout=120s` |

## Cluster and auth checks

```bash
# check cluster connectivity
kubectl cluster-info

# check current context and user
kubectl config current-context
kubectl auth whoami

# get API server URL
kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}'

# extract bearer token (e.g., for registry login)
kubectl config view --raw -o jsonpath='{.users[0].user.token}'
```

## Server-side filtering

Always filter before the data reaches the client.

```bash
# label selectors — most versatile, works on all resources
kubectl get pods -l app=myapp,version=v2
kubectl get pods -l 'app in (frontend,backend)'
kubectl get pods -l '!canary'

# field selectors — limited but useful
# pods support: status.phase, spec.nodeName, spec.restartPolicy, spec.serviceAccountName
# most other resources: only metadata.name, metadata.namespace
kubectl get pods --field-selector status.phase!=Running
kubectl get pods -A --field-selector spec.nodeName=worker-3

# combine both
kubectl get pods -l app=web --field-selector status.phase=Running

# prefer -n over --field-selector metadata.namespace=X
kubectl get pods -n myproject
```

## Custom columns

Best for 2-4 fields in readable tabular output:

```bash
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,NODE:.spec.nodeName --no-headers

kubectl get deployments -o custom-columns=NAME:.metadata.name,READY:.status.readyReplicas,DESIRED:.spec.replicas --no-headers

kubectl get crd -o custom-columns=NAME:.metadata.name,GROUP:.spec.group,SCOPE:.spec.scope --no-headers
```

## jsonpath quick reference

Use for 1-2 field extractions without jq:

```bash
# single value
kubectl get pod foo -o jsonpath='{.status.phase}'

# range iteration
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'

# filter expression
kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}'

# condition status
kubectl get pod foo -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}'
```

**Limitations**: no regex, no arithmetic, no sorting, no grouping. Switch to jq for those.

## jq recipes

Always output as `@tsv` for compact tabular data.

```bash
# pod status summary
kubectl get pods -A -o json | jq -r '
  .items[] | [.metadata.namespace, .metadata.name, .status.phase] | @tsv'

# non-ready pods only
kubectl get pods -A -o json | jq -r '
  .items[] | select(.status.phase != "Running") |
  [.metadata.namespace, .metadata.name, .status.phase] | @tsv'

# pods with highest restart counts (top 10)
kubectl get pods -A -o json | jq -r '
  [.items[] | {ns: .metadata.namespace, name: .metadata.name,
   restarts: ([.status.containerStatuses[]?.restartCount] | add // 0)}]
  | sort_by(-.restarts) | .[:10][] | [.ns, .name, .restarts] | @tsv'

# unique container images
kubectl get pods -A -o json | jq -r '[.items[].spec.containers[].image] | unique[]'

# resource count by namespace
kubectl get pods -A -o json | jq '
  .items | group_by(.metadata.namespace) |
  map({ns: .[0].metadata.namespace, count: length}) | sort_by(-.count)'

# CRD instance conditions (e.g., InferenceService readiness)
kubectl get inferenceservices -A -o json | jq -r '
  .items[] | [.metadata.namespace, .metadata.name,
  (.status.conditions[]? | select(.type=="Ready") | .status)] | @tsv'

# CRD inventory by API group
kubectl get crd -o json | jq -r '
  .items[] | [.metadata.name, .spec.group, (.spec.versions[].name | tostring)] | @tsv'

# operator versions (OLM CSV)
kubectl get csv -A -o json | jq -r '
  .items[] | [.metadata.namespace, .metadata.name, .spec.version] | @tsv'
```

## Batch and efficiency patterns

```bash
# get multiple specific resources in one call
kubectl get pod foo bar baz -o custom-columns=NAME:.metadata.name,STATUS:.status.phase --no-headers

# delete by label, not loop
kubectl delete pods -l app=test

# apply a directory
kubectl apply -f ./manifests/

# apply a kustomize overlay
kubectl apply -k ./overlays/dev/

# diff before apply (exit code 0 = no diff, 1 = has diff)
kubectl diff -f manifest.yaml

# wait instead of poll loop — always prefer over sleep+poll
kubectl wait --for=condition=Ready pod -l app=myapp --timeout=120s
kubectl wait --for=delete pod/foo --timeout=60s
kubectl wait --for=condition=Available deployment/myapp --timeout=120s
kubectl wait --for=condition=Established crd/myresources.example.com --timeout=300s
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/myns --timeout=60s

# check CRD existence
kubectl get crd inferenceservices.serving.kserve.io -o name --ignore-not-found

# check API group availability
kubectl api-resources --api-group=serving.kserve.io --no-headers
```

## OpenShift-specific (oc only)

Use `oc` only for subcommands that don't exist in kubectl:

```bash
# login (no kubectl equivalent)
oc login -u kubeadmin -p <password> https://api.cluster:6443

# project switching (shorthand for kubectl config set-context)
oc project myproject
```

OpenShift CRDs (Routes, ClusterVersion, ClusterOperators) are standard CRDs — use `kubectl` to query them:

```bash
# route URLs
kubectl get routes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.host}{"\n"}{end}'

# route admission status
kubectl get route myroute -o jsonpath='{.status.ingress[0].conditions[0].status}'

# cluster version
kubectl get clusterversion -o jsonpath='{.items[0].status.desired.version}'

# cluster operator health (compact)
kubectl get co -o custom-columns=NAME:.metadata.name,AVAIL:.status.conditions[?(@.type=="Available")].status,DEGR:.status.conditions[?(@.type=="Degraded")].status --no-headers
```

## Anti-patterns — never do these

| Do not | Why | Do instead |
|--------|-----|------------|
| `-o yaml` | Hundreds of lines per resource | `-o jsonpath` or `-o json \| jq` for specific fields |
| `kubectl describe` | Unstructured text, unparseable | `-o json \| jq` for conditions, events, status |
| `kubectl get pods \| grep Running` | Fragile text parsing | `--field-selector status.phase=Running` |
| Loop: `for p in $(kubectl get pods -o name); do kubectl get $p -o json; done` | N+1 queries | Single `kubectl get pods -o json \| jq` |
| `kubectl get all -A` | Unbounded, returns everything | Query specific resource types with selectors |
| `kubectl api-resources` (unfiltered) | ~100 lines | `--api-group=apps` or `--namespaced=true` |
| `kubectl logs pod` (no tail) | Unbounded output | `--tail=50` or `--since=5m` |
| `grep` / `awk` on kubectl output | Fragile, columns shift | jq or jsonpath |
| `oc` for standard k8s operations | Unnecessary dependency | `kubectl` works for all standard resources including OpenShift CRDs |
