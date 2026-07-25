# Concurrency, I/O, and latency

Use [`guide.md`](guide.md) for operational diagnosis of:

- async critical paths and continuation delay;
- ThreadPool starvation and blocking;
- lock ownership, contention, fairness, and convoys;
- queues, backpressure, timers, and wakeups;
- file, network, HTTP, DNS, TLS, database, and dependency latency;
- distributed tracing and UI dispatcher latency.

Pair it with the target [`../platforms/`](../platforms/index.md) guide for scheduler and OS I/O evidence.
