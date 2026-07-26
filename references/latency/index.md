# Concurrency, I/O, and latency

Use [`guide.md`](guide.md) for operational diagnosis of async critical paths, ThreadPool starvation, locks, queues, backpressure, timers, file/network/database I/O, distributed tracing, and UI dispatcher latency.

## Review guardrails

- Separate on-CPU execution, runnable delay, blocked/off-CPU time, queueing, dependency time, and throttling.
- A hot wait primitive identifies where a thread waited, not who owned the resource or why the protected work was long.
- Measure queue depth, arrival rate, service time, throughput, rejection/drop behavior, and p50/p95/p99 latency together.
- Preserve cancellation, timeout, ordering, fairness, and backpressure semantics when optimizing concurrency.
- Correlate logical async context (`Activity`, request/operation IDs) with physical thread/scheduler evidence.
- Do not add ThreadPool threads or parallelism without proving whether the workload is blocking, CPU-saturated, dependency-bound, or contention-bound.

Pair it with [`../runtime/index.md`](../runtime/index.md) for managed scheduling and stacks and [`../platforms/index.md`](../platforms/index.md) for scheduler and OS I/O evidence.
