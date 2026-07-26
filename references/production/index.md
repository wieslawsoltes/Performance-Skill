# Production and containers

Use [`guide.md`](guide.md) for production-only incidents, diagnostic ports, `dotnet-monitor`, containers, Kubernetes, triggered or bounded collection, permissions, privacy, and artifact handling.

## Review guardrails

- Start with the lowest-overhead evidence that can answer the question; escalate collection depth only when needed.
- Bound duration, buffers, artifact size, and trigger frequency before production capture.
- Record host and cgroup CPU/memory limits, PID namespace, diagnostic socket path, security context, and profiler capabilities.
- Do not default to privileged containers. Grant only the capabilities and mounts required by the selected tool.
- Treat traces, dumps, logs, database spans, and packet data as sensitive. Define storage, transfer, access, and deletion policy before capture.
- Preserve matching binaries, runtime identity, build IDs, and symbols without exposing proprietary artifacts.
- Reproduce the incident in a safer environment when invasive heap, syscall, or GPU capture would materially perturb production.

Pair this domain with the relevant runtime, memory, latency, startup, GPU, and platform references. Container boundaries do not change ownership; they add resource, namespace, permission, and observability constraints.
