# Kustomize Config Review

Review and update generated kustomize configuration after scaffolding:

1. `config/default/kustomization.yaml` — verify namespace and resource list
2. `config/manager/manager.yaml` — set resource limits and image
3. For webhooks, uncomment in `config/crd/kustomization.yaml`:
   - `patches/webhook_in_<kind>.yaml`
   - `patches/cainjection_in_<kind>.yaml`
4. For webhooks, enable in `config/default/kustomization.yaml`:
   - `../certmanager`
   - `../webhook`
