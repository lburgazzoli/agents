# Main Configuration Reference

Kubebuilder generates a flat `cmd/main.go` with `flag.Parse()`. Rewrite it into a cobra+viper subcommand structure with production-ready cache and client configuration.

## Directory Structure

```
cmd/
  main.go                    # Root cobra command, registers subcommands
  operator/
    operator.go              # Operator subcommand: manager setup + start
```

## cmd/main.go

```go
package main

import (
    "os"

    "github.com/spf13/cobra"
    ctrl "sigs.k8s.io/controller-runtime"

    "github.com/<module>/cmd/operator"
)

func main() {
    root := &cobra.Command{
        Use:          "<project-name>",
        SilenceUsage: true,
    }

    root.AddCommand(operator.NewCommand())

    if err := root.ExecuteContext(ctrl.SetupSignalHandler()); err != nil {
        os.Exit(1)
    }
}
```

## cmd/operator/operator.go

```go
package operator

import (
    "fmt"
    "strings"

    "github.com/spf13/cobra"
    "github.com/spf13/viper"
    ctrl "sigs.k8s.io/controller-runtime"
    "sigs.k8s.io/controller-runtime/pkg/cache"
    "sigs.k8s.io/controller-runtime/pkg/client"
    "sigs.k8s.io/controller-runtime/pkg/healthz"
    "sigs.k8s.io/controller-runtime/pkg/log/zap"
    metricsserver "sigs.k8s.io/controller-runtime/pkg/metrics/server"
)

func NewCommand() *cobra.Command {
    cmd := &cobra.Command{
        Use:   "operator",
        Short: "Start the operator",
        PreRunE: func(cmd *cobra.Command, _ []string) error {
            viper.SetEnvPrefix("OPERATOR")
            viper.SetEnvKeyReplacer(strings.NewReplacer("-", "_"))
            viper.AutomaticEnv()
            return viper.BindPFlags(cmd.Flags())
        },
        RunE: run,
    }

    f := cmd.Flags()
    f.String("metrics-addr", ":8080", "Metrics bind address (0 to disable)")
    f.String("health-probe-addr", ":8081", "Health probe bind address")
    f.String("pprof-addr", "", "Pprof bind address (empty = disabled)")
    f.Bool("leader-elect", true, "Enable leader election")
    f.String("leader-election-id", "<project-name>-lock", "Leader election lock name")

    return cmd
}

func run(cmd *cobra.Command, _ []string) error {
    ctrl.SetLogger(zap.New(zap.UseDevMode(false)))

    mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
        Scheme: scheme,
        Metrics: metricsserver.Options{
            BindAddress: viper.GetString("metrics-addr"),
        },
        HealthProbeBindAddress:        viper.GetString("health-probe-addr"),
        PprofBindAddress:              viper.GetString("pprof-addr"),
        LeaderElection:                viper.GetBool("leader-elect"),
        LeaderElectionID:              viper.GetString("leader-election-id"),
        LeaderElectionReleaseOnCancel: true,

        Cache: cache.Options{
            DefaultTransform: cache.TransformStripManagedFields(),
        },

        Client: client.Options{
            Cache: &client.CacheOptions{
                DisableFor: []client.Object{},
            },
        },
    })
    if err != nil {
        return fmt.Errorf("creating manager: %w", err)
    }

    // Register controllers here.

    if err := mgr.AddHealthzCheck("healthz", healthz.Ping); err != nil {
        return fmt.Errorf("setting up health check: %w", err)
    }
    if err := mgr.AddReadyzCheck("readyz", healthz.Ping); err != nil {
        return fmt.Errorf("setting up ready check: %w", err)
    }

    return mgr.Start(cmd.Context())
}
```

## Defaults

- **Leader election**: enabled by default (`--leader-elect` defaults to `true`)
- **Replicas**: if webhooks are configured, set replicas to 2 in `config/manager/manager.yaml` (webhook availability requires multiple pods)

## Cache Configuration

`cache.TransformStripManagedFields()` is set as `DefaultTransform` — strips `managedFields` from all cached objects, reducing memory.

Per-type overrides via `ByObject`:

```go
Cache: cache.Options{
    DefaultTransform: cache.TransformStripManagedFields(),
    ByObject: map[client.Object]cache.ByObject{
        &corev1.Secret{}: {
            Label: labels.SelectorFromSet(labels.Set{
                "app.kubernetes.io/managed-by": "<project-name>",
            }),
        },
    },
},
```

## Client Configuration

Bypass cache for types that must always read fresh from the API server:

```go
Client: client.Options{
    Cache: &client.CacheOptions{
        DisableFor: []client.Object{
            &corev1.Secret{},
            &corev1.ConfigMap{},
        },
    },
},
```

## Viper Environment Variables

With `SetEnvPrefix("OPERATOR")` and `SetEnvKeyReplacer("-", "_")`:

| Flag | Env Var |
|------|---------|
| `--metrics-addr` | `OPERATOR_METRICS_ADDR` |
| `--health-probe-addr` | `OPERATOR_HEALTH_PROBE_ADDR` |
| `--leader-elect` | `OPERATOR_LEADER_ELECT` |
| `--leader-election-id` | `OPERATOR_LEADER_ELECTION_ID` |
| `--pprof-addr` | `OPERATOR_PPROF_ADDR` |

Precedence: explicit flag > env var > default.

## Dependencies

```bash
go get github.com/spf13/cobra
go get github.com/spf13/viper
```
