# Concurrency, I/O, and latency

Use [`guide.md`](guide.md) for operational diagnosis of async critical paths, ThreadPool starvation, locks, queues, backpressure, timers, file/network/database I/O, distributed tracing, and UI dispatcher latency. Consult [`../command-reference.md`](../command-reference.md) before executing profiler commands.[^command-reference]

## Review guardrails

- Separate on-CPU execution, runnable delay, blocked/off-CPU time, queueing, dependency time, and throttling.
- A hot wait primitive identifies where a thread waited, not who owned the resource or why the protected work was long.
- Measure queue depth, arrival rate, service time, throughput, rejection/drop behavior, and p50/p95/p99 latency together.
- Preserve cancellation, timeout, ordering, fairness, and backpressure semantics when optimizing concurrency.
- Correlate logical async context (`Activity`, request/operation IDs) with physical thread/scheduler evidence.
- Do not add ThreadPool threads or parallelism without proving whether the workload is blocking, CPU-saturated, dependency-bound, or contention-bound.

Pair it with [`../runtime/index.md`](../runtime/index.md) for managed scheduling and stacks and [`../platforms/index.md`](../platforms/index.md) for scheduler and OS I/O evidence.

## Documentation footnotes

[^command-reference]: [`../command-reference.md`](../command-reference.md).
[^dotnet-trace]: Microsoft, [`dotnet-trace`](https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-trace).
[^activity]: Microsoft, [distributed tracing and `Activity`](https://learn.microsoft.com/dotnet/core/diagnostics/distributed-tracing).
[^perf-sched]: Linux, [`perf-sched(1)`](https://man7.org/linux/man-pages/man1/perf-sched.1.html).
[^bcc]: iovisor, [BCC tools](https://github.com/iovisor/bcc).
[^wpa]: Microsoft, [Windows Performance Analyzer](https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-analyzer).
[^xctrace]: Apple/Xcode, [`xctrace(1)`](https://keith.github.io/xcode-man-pages/xctrace.1.html).