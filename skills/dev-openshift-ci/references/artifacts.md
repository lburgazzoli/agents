# OpenShift CI artifacts

Layout of a run and queries for the cluster state collected by the `gather-*` steps.

## Where runs live

```
gs://test-platform-results-public/pr-logs/pull/<org>_<repo>/<pr>/<job>/<build_id>/
https://prow.ci.openshift.org/view/gs/test-platform-results-public/pr-logs/pull/<org>_<repo>/<pr>/<job>/<build_id>
```

The Prow URL is the `gs://` path with a different prefix. `<job>` is `pull-ci-<org>-<repo>-<branch>-<test>`; the GitHub status context for it is `ci/prow/<test>`. `<job>/latest-build.txt` holds the newest build ID, including runs still in progress.

`scripts/main.py fetch` mirrors a run under `.context/openshift-ci/<org>_<repo>/<pr>/<job>/<build_id>/` with the same relative paths.

## Files of a run

| Path | Content |
|------|---------|
| `prowjob.json` | Job spec and status: job name, refs, PR, commit, state, start and completion time. |
| `started.json`, `finished.json` | Start time; result (`SUCCESS`/`FAILURE`) and `passed`. No `finished.json` means the run has not ended. |
| `build-log.txt` | ci-operator's own log for the whole job. Includes the output of the failed step, so it is the largest log. |
| `artifacts/ci-operator-step-graph.json` | Every ci-operator step with `failed`, `duration` (nanoseconds) and, for the test, its `substeps`. |
| `artifacts/junit_operator.xml` | The same steps as junit. Not test results. |
| `artifacts/ci-operator.log` | ci-operator log as JSON Lines. |
| `artifacts/build-logs/<image>.log` | Image build logs. |
| `artifacts/build-resources/` | `pods.json`, `events.json`, `builds.json` of the CI namespace that ran the job (not the test cluster). |
| `artifacts/<test>/<step>/` | One directory per step of the test: `build-log.txt`, `finished.json`, and `artifacts/` with whatever the step wrote (junit reports, logs). |

`<test>` is the last part of the job name. Steps run in order: pre steps (cluster claim or `ipi-*` install, setup), the test steps, then post steps (`gather-*`).

## Gather steps

Not part of the triage tier. Fetch with `scripts/main.py fetch <gs_url> --step <name>` or `--tier gather`.

| Step | Content |
|------|---------|
| `gather-extra` | Cluster-wide resource dumps as JSON, pod logs, node journals, an `oc adm inspect` tree. The most useful one. |
| `gather-must-gather` | `oc adm must-gather` output: the same `inspect` tree, limited to the OpenShift platform namespaces. |
| `gather-audit-logs` | API server audit logs. |

`gather-extra/artifacts/metrics/prometheus.tar.gz` is several hundred MB and is skipped unless `--tier all` is used. Without it `gather-extra` is still about 260 MB in 7,700 files.

### `gather-extra/artifacts/`

| Path | Content |
|------|---------|
| `<resource>.json` | A Kubernetes `List` of that resource across all namespaces: `pods.json`, `events.json`, `deployments.json`, `clusteroperators.json`, `clusterversion.json`, `nodes.json`, `clusterserviceversions.json`, `subscriptions.json`, and more. |
| `oc_cmds/<resource>` | The same resources as `oc get` table text. |
| `pods/<namespace>_<pod>_<container>.log` | Container logs. `…_previous.log` is the log of the container's previous instance, present after a restart. |
| `nodes/<node>/journal` | Node journal, gzip-compressed: read with `zcat -f`. A 160-byte file means the node could not be reached. |
| `inspect/namespaces/<ns>/<group>/<resource>.yaml` | Resources per namespace, for the API groups the inspect covered. |
| `inspect/namespaces/<ns>/pods/<pod>/<container>/<container>/logs/current.log` | Container logs, per namespace. |
| `inspect/cluster-scoped-resources/<group>/<resource>/` | Cluster-scoped resources, mostly platform groups. |

Custom resources are covered unevenly: the `inspect` tree holds only some API groups, and an operator's own cluster-scoped CRs are often absent. When the CR you need is not there, say so; its state at failure time is usually printed by the test itself in the step's `build-log.txt`.

## Queries

`G` is `<run dir>/artifacts/<test>/gather-extra/artifacts`. Timestamps are UTC, as in the test logs, so events can be matched to the time of a failure.

The dumps are taken after the tests and their cleanup. `pods.json` and `deployments.json` describe the end of the job; `events.json` and the pod logs are what still describe the moment of the failure.

Warning events of a namespace grouped by reason, with count and first occurrence. Start here: it shows the kinds of trouble in a few lines.

```bash
jq -r --arg ns '<namespace>' '.items | map(select(.type == "Warning" and .involvedObject.namespace == $ns))
  | group_by(.reason + "|" + .involvedObject.kind)
  | map([(length | tostring), .[0].reason, .[0].involvedObject.kind, (map(.firstTimestamp // .eventTime) | min), (.[0].message | .[0:200])] | @tsv) | .[]' \
  "$G/events.json"
```

Warning events, oldest first:

```bash
jq -r '.items | map(select(.type == "Warning")) | sort_by(.lastTimestamp // .eventTime)
  | .[] | [(.lastTimestamp // .eventTime), .involvedObject.namespace, .involvedObject.kind + "/" + .involvedObject.name, .reason, (.message | .[0:200])] | @tsv' \
  "$G/events.json"
```

Narrow to one namespace by adding `and .involvedObject.namespace == "<ns>"` to the `select`.

Pods that are not healthy:

```bash
jq -r '.items[] | select(.status.phase != "Succeeded")
  | . as $p | (.status.containerStatuses // [])[] | select(.ready | not)
  | [$p.metadata.namespace, $p.metadata.name, .name, $p.status.phase, (.restartCount | tostring), (.state | keys[0]), (.state[] | .reason // "")] | @tsv' \
  "$G/pods.json"
```

Pods that could not be scheduled or started (no container status yet):

```bash
jq -r '.items[] | select(.status.phase == "Pending")
  | [.metadata.namespace, .metadata.name, ((.status.conditions // []) | map(select(.status == "False")) | map(.reason + ": " + (.message // "")) | join("; ") | .[0:200])] | @tsv' \
  "$G/pods.json"
```

Deployments short of replicas:

```bash
jq -r '.items[] | select((.status.readyReplicas // 0) < (.spec.replicas // 1))
  | [.metadata.namespace, .metadata.name, ((.status.readyReplicas // 0) | tostring) + "/" + (.spec.replicas | tostring)] | @tsv' \
  "$G/deployments.json"
```

Workloads the cluster's controllers never acted on. A Deployment with no `observedGeneration` was created but never picked up by the deployment controller; several of them, created over a long period, mean the control plane stopped working during the run and every later test timeout is a consequence:

```bash
jq -r '.items[] | select((.status.observedGeneration // 0) < .metadata.generation)
  | [.metadata.namespace, .metadata.name, .metadata.creationTimestamp, "observed=" + ((.status.observedGeneration // "none") | tostring)] | @tsv' \
  "$G/deployments.json"
```

Confirm with the event rate, which drops to almost nothing at the same moment, and with `gather-extra/build-log.txt`, where log collection errors per node show which kubelets were unreachable:

```bash
jq -r '.items[] | (.firstTimestamp // .eventTime) | .[0:15]' "$G/events.json" | sort | uniq -c
rg -c 'Authorization error|no such host|i/o timeout' "<run dir>/artifacts/<test>/gather-extra/build-log.txt"
```

Cluster operators that are degraded or unavailable (a platform problem, not the PR):

```bash
jq -r '.items[] | . as $o | .status.conditions[]
  | select((.type == "Degraded" and .status == "True") or (.type == "Available" and .status == "False"))
  | [$o.metadata.name, .type, .reason, (.message | .[0:200])] | @tsv' \
  "$G/clusteroperators.json"
```

Logs of a pod:

```bash
ls "$G/pods/" | rg '^<namespace>_<pod name prefix>'
rg -n -i 'error|panic|fatal' "$G/pods/<namespace>_<pod>_<container>.log" | cut -c1-300 | tail -40
```

Whether a kind was collected at all, and where:

```bash
ls "$G/inspect/namespaces/<namespace>/"
rg -l '^kind: <Kind>$' "$G/inspect" | head
```
