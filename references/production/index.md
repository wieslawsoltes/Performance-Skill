# Production and containers

Use [`guide.md`](guide.md) for production-only incidents, diagnostic ports, `dotnet-monitor`, containers, Kubernetes, triggered or bounded collection, permissions, privacy, and artifact handling. Consult [`../command-reference.md`](../command-reference.md) before executing collection commands.[^command-reference]

## Review guardrails

- Start with the lowest-overhead evidence that can answer the question; escalate collection depth only when needed.
- Bound duration, buffers, artifact size, and trigger frequency before production capture.
- Record host and cgroup CPU/memory limits, PID namespace, diagnostic socket path, security context, and profiler capabilities.
- Do not default to privileged containers. Grant only the capabilities and mounts required by the selected tool.
- Treat traces, dumps, logs, database spans, and packet data as sensitive. Define storage, transfer, access, and deletion policy before capture.
- Preserve matching binaries, runtime identity, build IDs, and symbols without exposing proprietary artifacts.
- Reproduce the incident in a safer environment when invasive heap, syscall, or GPU capture would materially perturb production.

Pair this domain with the relevant runtime, memory, latency, startup, GPU, and platform references. Container boundaries do not change ownership; they add resource, namespace, permission, and observability constraints.

## Documentation footnotes

[^command-reference]: [`../command-reference.md`](../command-reference.md).
[^dotnet-monitor]: Microsoft, [`dotnet-monitor`](https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-monitor).
[^diagnostic-port]: Microsoft, [diagnostic port](https://learn.microsoft.com/dotnet/core/diagnostics/diagnostic-port).
[^containers]: Microsoft, [collect diagnostics in containers](https://learn.microsoft.com/dotnet/core/diagnostics/diagnostics-in-containers).
[^kubernetes]: Kubernetes, [security context](https://kubernetes.io/docs/tasks/configure-pod-container/security-context/).
[^cgroup-v2]: Linux kernel, [cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html).