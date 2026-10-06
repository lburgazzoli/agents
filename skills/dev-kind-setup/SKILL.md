---
name: dev-kind-setup
description: Create a Kind cluster and install the latest cert-manager. Use when the user asks to create, start, or set up a local Kind cluster, or needs a throwaway Kubernetes cluster with cert-manager for testing webhooks or operators.
user-invocable: true
allowed-tools:
  - Bash
---

# Kind Cluster Setup

Create a Kind (Kubernetes in Docker) cluster with cert-manager installed.

## Input

The user's request may name the cluster (default: `kind`).

## Steps

1. Run `kind create cluster --name <cluster-name>`. Use the name the user gave, otherwise default to `kind`.
2. Wait for nodes to be `Ready`:
   ```
   kubectl wait --for=condition=Ready nodes --all --timeout=60s
   ```
3. Install the latest cert-manager:
   ```
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
   ```
4. Wait for cert-manager deployments to be available:
   ```
   kubectl wait --for=condition=Available deployment --all -n cert-manager --timeout=120s
   ```
5. Report the result: confirm cluster name, current kubectl context (`kubectl config current-context`), and cert-manager pod status (`kubectl get pods -n cert-manager`).
