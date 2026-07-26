# Managed runtime CPU, GC, allocation, JIT, and exception profiling

Use this reference when the dominant cost may be inside managed code or the CLR. Combine it with the relevant platform reference whenever native frames, scheduling, kernel activity, or total-process ownership matter.

## Tool discovery and version pinning

Prefer repository-local tools so another agent can reproduce the collection.

```bash
dotnet new tool-manifest
dotnet tool install dotnet-counters
dotnet tool install dotnet-trace
dotnet tool install dotnet-stack
dotnet tool install dotnet-dump
dotnet tool install dotnet-gcdump
dotnet tool install dotnet-symbol

dotnet tool list
```

Record tool versions beside every artifact. Do not assume syntax or built-in profiles are identical across versions.

## Process discovery and diagnostics availability

```bash
dotnet-counters ps
dotnet-trace ps
dotnet-dump ps
```

When attach fails, check:

- target and tool run as compatible users;
- diagnostics have not been disabled;
- diagnostic socket or pipe permissions;
- on Linux/macOS, the tool and target share `TMPDIR`;
- container PID namespace visibility;
- architecture compatibility;
- process lifetime and whether the wrong `dotnet` child was selected.

For framework-dependent processes identify the target by PID, command line, start time, and parent/child tree, not only the executable name.

## Runtime-counter baseline

Record counters for the full deterministic workload, not only an interactive glance.

```bash
mkdir -p artifacts/performance/runtime

dotnet-counters collect \
  --process-id <PID> \
  --refresh-interval 1 \
  --format csv \
  --output artifacts/performance/runtime/counters.csv \
  --counters System.Runtime
```

At minimum inspect correlated trends for:

- process CPU and working set;
- GC heap size, committed bytes, allocation rate, and Gen 0/1/2 counts;
- time in GC and LOH size where exposed;
- exception rate;
- ThreadPool thread count, queue length, and completed-work rate;
- monitor lock contention.

Interpret rates over meaningful intervals. A one-second spike is not equivalent to sustained pressure.

## Managed CPU sampling

Attach to a warm process using the current standard profiles:

```bash
dotnet-trace collect \
  --process-id <PID> \
  --profile dotnet-common,dotnet-sampled-thread-time \
  --duration 00:00:00:30 \
  --output artifacts/performance/runtime/cpu.nettrace
```

Export a Speedscope view only as a derived artifact when useful:

```bash
dotnet-trace convert \
  --format Speedscope \
  --output artifacts/performance/runtime/cpu \
  artifacts/performance/runtime/cpu.nettrace
```

The historical `cpu-sampling` profile was removed from standard `dotnet-trace collect`. It remains valid for the separate Linux `collect-linux` perf-based workflow.

Launch for startup or short-lived workloads:

```bash
dotnet-trace collect \
  --profile dotnet-common,dotnet-sampled-thread-time \
  --duration 00:00:00:30 \
  --show-child-io \
  --output artifacts/performance/runtime/startup.nettrace \
  -- dotnet exec ./App.dll
```

Analysis procedure:

1. identify the workload time range;
2. filter to the target process and relevant threads;
3. inspect inclusive cost first;
4. expand callers and callees;
5. separate application frames, runtime/JIT/GC frames, framework code, and P/Invoke transitions;
6. distinguish useful work, spin/polling, exception handling, allocation helpers, and sampling artifacts;
7. correlate with process CPU and platform-native stacks.

Sampling answers where CPU time was observed. It does not provide exact call counts or exact per-call cost.

## Runtime event tracing

Use built-in profiles when available and inspect current help before using custom provider masks:

```bash
dotnet-trace collect --help
```

Useful current profiles include:

- `dotnet-common` for lightweight GC, loader, JIT, exception, and threading events;
- `dotnet-sampled-thread-time` for managed stack sampling;
- `gc-collect` for low-overhead GC collections;
- `gc-verbose` for GC plus sampled allocations;
- `database` for supported ADO.NET and Entity Framework commands.

Keep duration and buffers bounded. Allocation-heavy traces can perturb the workload and become very large. Store raw `.nettrace` files even when also exporting stacks or reports.

## Allocation profiling

Use three layers:

1. allocation rate from counters;
2. sampled allocation stacks from runtime traces or a managed profiler;
3. live-object and retention evidence from GC dumps or full dumps.

Questions to answer:

- Which types allocate the most bytes and objects?
- Which call stacks allocate them?
- Are allocations transient or promoted?
- Do objects survive Gen 2 or equivalent full collections?
- Is LOH or pinned-object pressure involved?
- Is allocation caused by boxing, iterators/state machines, closures, strings, arrays, serialization, reflection, or interop wrappers?

Do not infer retention from allocation volume. A type may dominate allocation traffic while leaving no live objects.

## GC pause and heap analysis

Correlate:

- collection start/end and generation;
- pause duration and suspension time;
- allocation rate before the collection;
- promoted bytes and surviving objects;
- heap size before/after;
- LOH and pinned-object behavior;
- CPU utilization and latency during pauses;
- container or process memory limits.

Typical classifications:

- frequent Gen 0 with low pause: throughput cost from transient allocation;
- frequent Gen 1/2: promotion, insufficient ephemeral space, or retained graphs;
- long blocking Gen 2: large live set, fragmentation, pinning, pressure, or heap limits;
- high time in GC with moderate allocation: expensive scanning/promotion or constrained heap configuration;
- large committed heap with small live bytes: fragmentation, retained segments, heap policy, or delayed decommit—not automatically a leak.

When server GC is enabled, inspect each heap and NUMA/CPU topology rather than only aggregate values.

## JIT, tiering, ReadyToRun, and dynamic PGO

Separate cold and warm behavior. Capture:

- method compilation duration and compiled code size;
- tier transitions;
- ReadyToRun usage versus JIT fallback;
- generic instantiation and reflection-heavy paths;
- dynamic PGO warm-up effects;
- code-cache growth;
- first-call latency for hot paths.

Example deployment variants:

```bash
# framework-dependent baseline
dotnet ./App.dll

# ReadyToRun publish
dotnet publish -c Release -r <RID> -p:PublishReadyToRun=true

# NativeAOT publish
dotnet publish -c Release -r <RID> -p:PublishAot=true
```

Do not disable tiering or PGO merely to simplify a trace unless the experiment explicitly studies those features. Record every environment override and restore production defaults for final validation.

## Exceptions

High exception rates can dominate CPU and allocation while remaining hidden in normal logs. Investigate:

- first-chance exception type and throw stack;
- repeated parse/probe/fallback exceptions;
- cancellation exceptions on hot paths;
- exception-based feature detection;
- retries that repeatedly construct exceptions;
- logging and stack-formatting cost.

Do not remove exceptions required for correctness. Replace exception-driven expected control flow only when semantics remain equivalent.

## ThreadPool and work scheduling

Correlate queue length, worker count, work-item throughput, CPU, continuations, blocking calls, and timer/polling frequency.

Classification:

- rising queue, low CPU, growing threads: blocking or starvation;
- rising queue, saturated CPU: insufficient capacity or excessive work;
- many workers with low throughput: contention, external waits, or tiny work-item overhead;
- sawtooth latency with thread injection: starvation recovery;
- high timer/wakeup rate: polling or overly granular scheduling.

Use repeated stack snapshots to find persistent blockers:

```bash
for i in 1 2 3 4 5; do
  dotnet-stack report --process-id <PID> > "artifacts/performance/runtime/stack-$i.txt"
  sleep 1
done
```

## Locks and contention

Use runtime contention events plus platform scheduling evidence. Identify lock or synchronization identity where possible, owner/waiter stacks, hold duration, waiter count, nesting, convoying, reader/writer imbalance, global caches, allocator locks, and UI/render/worker synchronization.

A hot `Monitor.Enter`, futex, semaphore, or kernel-wait frame is an entry point, not the root cause. Find the owner and protected work.

## Async investigations

Physical thread stacks do not always show the logical async chain. Correlate task events, `Activity` identifiers, request IDs, continuation scheduling delay, ThreadPool queueing, external I/O spans, and dispatcher transitions.

Look for:

- sync-over-async (`.Result`, `.Wait()`, blocking `GetAwaiter().GetResult()`);
- excessive `Task.Run` around already-asynchronous work;
- serial awaits that could safely overlap;
- unbounded fan-out;
- cancellation and timeout storms;
- async state-machine allocation on hot paths;
- continuations forced onto a busy UI thread.

## Dumps and SOS

Collect a full dump when live tracing cannot answer object roots, deadlocks, finalization, or combined state questions.

```bash
dotnet-dump collect \
  --process-id <PID> \
  --type Full \
  --output artifacts/performance/runtime/process.dmp

dotnet-dump analyze artifacts/performance/runtime/process.dmp
```

Useful commands:

```text
clrthreads
clrstack -all
threadpool
syncblk
dumpheap -stat
dumpheap -type Namespace.Type
gcroot <address>
eeheap -gc
gchandles
finalizequeue
```

Use `dotnet-symbol` or platform symbol tooling when the dump was collected elsewhere. Record runtime build identity and retain matching binaries. Treat dumps as sensitive artifacts.

## Validation

After a fix, repeat the same workload and report:

- process CPU and wall time;
- hottest inclusive managed stacks;
- allocation rate and bytes per operation;
- GC pause p50/p95/p99 and time in GC;
- live heap after equivalent full-collection points;
- exception rate;
- ThreadPool queue and contention;
- startup first-run and warm-run latency where relevant.

A reduction in one runtime metric is not sufficient if total wall time, tail latency, native CPU, memory, diagnostics, or correctness regresses.
