# Production, containers, remote diagnostics, and low-overhead collection

Use this reference when the issue occurs only in production, under orchestration, inside containers, on remote machines, or under security/resource constraints.

## Safety rules

Before collecting:

- define the symptom and trigger condition;
- estimate artifact size and collection overhead;
- verify free disk and memory headroom;
- protect secrets and personal data;
- set duration and buffer limits;
- avoid repeated full dumps of very large processes;
- obtain approval for packet capture, heap dumps, or payload-rich traces;
- preserve exact UTC timestamps and host/container identity.

Start with counters and bounded traces. Escalate to dumps or high-volume allocation events only when evidence requires them.

## dotnet-monitor

`dotnet-monitor` can expose metrics and collect traces, dumps, logs, and GC dumps on demand or through collection rules.

Install as a tool or use the official container image according to deployment policy:

```bash
dotnet tool install --global dotnet-monitor
dotnet-monitor --version
```

For containerized deployments, a sidecar is often preferable to modifying the application image. Share the diagnostics socket/volume and ensure compatible user/group permissions.

Do not expose the diagnostic HTTP endpoint publicly. Configure authentication, TLS/network isolation, and collection limits appropriate to the environment.

## Diagnostic ports and sockets

When standard PID attach is impossible, use .NET diagnostic ports. Record all environment variables and startup arguments because suspend/connect modes can change application startup behavior.

Check:

- socket path exists and is shared with the collector;
- both containers/processes can read/write it;
- UID/GID and SELinux/AppArmor policy;
- target runtime supports the chosen mode;
- startup suspension cannot leave the service unavailable if collector attachment fails.

## Container collection models

### Tool inside the application container

Advantages: simple PID/socket visibility. Risks: larger image, extra attack surface, profiler competes inside the same memory/CPU limit.

### Host collection

Advantages: minimal app-image change. Risks: PID namespaces, permissions, filesystem/socket access, and host policy.

### Sidecar collection

Advantages: separate tooling lifecycle and artifact volume. Risks: shared PID namespace or diagnostic socket setup, permissions, and sidecar resource limits.

Document which model was used.

## Linux container requirements

Depending on the tool, collection may require:

- `CAP_PERFMON`;
- `CAP_SYS_PTRACE`;
- occasionally broader capabilities under restrictive environments;
- relaxed seccomp profile;
- host or shared PID namespace;
- mounted tracefs/debugfs;
- access to `/proc` and `/dev/dri` for GPU work;
- matching architecture and libc/tool compatibility.

Do not run privileged by default. Add the minimum capability required and remove it after the investigation.

## Resource-limit context

Record cgroup/container:

- CPU quota and cpuset;
- throttled periods/time;
- memory current, peak, and limit;
- swap limit;
- OOM events;
- PID/thread limits;
- I/O limits;
- GPU device assignment and memory budget.

A profiler can trigger an OOM or CPU throttling that does not occur without it. Report collector overhead and resource competition.

## Triggered collection

Prefer condition-based collection for intermittent problems. Useful triggers include:

- CPU above threshold for N seconds;
- GC heap or working set above threshold;
- exception-rate spike;
- ThreadPool queue growth;
- request p99 breach;
- sustained frame hitches;
- process exit/crash;
- health-check failure.

Use cooldowns and collection-count limits to prevent artifact storms.

## Bounded trace strategy

For high-frequency incidents use circular or bounded buffers where supported. Capture enough pre-trigger history to explain buildup and enough post-trigger time to observe recovery.

Record:

```text
trigger timestamp
collection start/end
clock source and timezone
process/container restart count
host load
request/workload identifier
artifact checksum and location
```

## Remote symbol and binary retention

For dumps and native traces retain:

- exact application binaries;
- runtime and native dependencies;
- PDBs/dSYM/debug files according to security policy;
- build ID/UUID/module identity;
- source commit and build manifest.

Use `dotnet-symbol` and platform symbol servers where appropriate. Never publish private symbols unintentionally.

## Crash and hang artifacts

For crashes collect OS crash reports/core dumps plus managed dumps where supported. For hangs collect repeated stacks before a full dump when possible.

A single hang dump shows state at one instant. Repeated stacks or a scheduling trace distinguishes a permanent deadlock from slow progress.

## Kubernetes guidance

Record pod, namespace, node, container ID, image digest, restart count, requests/limits, QoS class, and node pressure.

Use ephemeral debug containers or sidecars only when cluster policy permits. Ensure artifacts are copied to durable storage before the pod is evicted or restarted.

Correlate with:

- pod CPU throttling;
- memory pressure/OOM kill;
- node disk/network pressure;
- readiness/liveness failures;
- autoscaling events;
- rescheduling and cold caches;
- service-mesh/proxy latency.

## Privacy and artifact handling

Heap dumps, traces, logs, SQL spans, and packet captures can contain secrets, user data, paths, URLs, tokens, and payloads.

Apply:

- access control;
- encryption at rest/in transit;
- retention limits;
- redaction where possible;
- secure deletion;
- documented artifact ownership.

Do not commit raw production dumps or traces to Git.

## Production validation

After a fix or mitigation, verify under equivalent traffic and limits:

- symptom trigger no longer occurs;
- CPU/throttling and memory/OOM behavior;
- p95/p99 latency and error rate;
- queue and dependency metrics;
- restart/recovery behavior;
- profiler/telemetry overhead;
- no diagnostic endpoint or elevated capability remains exposed.

State clearly when production evidence is observational rather than a controlled causal experiment.