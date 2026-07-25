# Core .NET performance workflow

## Controlled workload

Capture repository commit, build configuration, target framework, runtime and SDK versions, OS, architecture, power mode, deployment model, input data, warm-up policy, measurement duration, and run count.

```bash
dotnet --info
dotnet build -c Release
```

Profile the real published form when deployment affects startup, JIT, code size, native dependencies, or runtime behavior.

```bash
dotnet publish -c Release -r <RID> --self-contained false
```

Prefer a deterministic script over manual interaction. For UI workloads define exact actions and frame count. For services define request rate, concurrency, payload, cache state, and duration.

## Portable first-level triage

Use repository-local tools where possible.

```bash
dotnet new tool-manifest
dotnet tool install dotnet-counters
dotnet tool install dotnet-trace
dotnet tool install dotnet-stack
dotnet tool install dotnet-dump
dotnet tool install dotnet-gcdump
```

Discover processes:

```bash
dotnet-counters ps
dotnet-trace ps
dotnet-dump ps
```

Monitor runtime health:

```bash
dotnet-counters monitor --process-id <PID> --counters System.Runtime
```

Collect comparable counter artifacts:

```bash
mkdir -p artifacts/performance
dotnet-counters collect \
  --process-id <PID> \
  --refresh-interval 1 \
  --format csv \
  --output artifacts/performance/counters.csv \
  --counters System.Runtime
```

Interpret correlated signals:

- high CPU with low allocation: compute, spin, native work, rendering, serialization, or contention;
- high allocation with frequent Gen 0/1: transient pressure;
- growing heap after full collections: retention or intentional cache growth;
- stable managed heap with growing RSS: native heap, mappings, graphics resources, JIT/code heaps, fragmentation, or OS caches;
- high GC time: allocation volume, promotion, LOH, pinning, or heap constraints;
- growing ThreadPool queue with low CPU: blocking, starvation, sync-over-async, or external latency.

## Managed CPU and runtime traces

```bash
dotnet-trace collect \
  --process-id <PID> \
  --profile cpu-sampling \
  --duration 00:00:30 \
  --format Speedscope \
  --output artifacts/performance/managed-cpu.speedscope.json
```

For startup, launch the application through the collector rather than attaching late.

```bash
dotnet-trace collect \
  --profile cpu-sampling \
  --format speedscope \
  --output artifacts/performance/startup.speedscope.json \
  -- dotnet exec ./App.dll
```

For GC/allocation scenarios collect runtime events. Provider masks are runtime- and scenario-specific; verify them against current documentation and tool output before relying on a custom mask.

Capture repeated live stacks for hangs or starvation:

```bash
dotnet-stack report --process-id <PID> > artifacts/performance/stacks.txt
```

## Managed heap and dumps

Collect at least two heap points around repeated workload execution.

```bash
dotnet-gcdump collect --process-id <PID> --output artifacts/performance/heap-01.gcdump
# repeat suspect workload
dotnet-gcdump collect --process-id <PID> --output artifacts/performance/heap-02.gcdump

dotnet-gcdump report artifacts/performance/heap-01.gcdump > artifacts/performance/heap-01.txt
dotnet-gcdump report artifacts/performance/heap-02.gcdump > artifacts/performance/heap-02.txt
```

For roots, locks, finalization, or comprehensive managed state:

```bash
dotnet-dump collect --process-id <PID> --type Full --output artifacts/performance/process.dmp
dotnet-dump analyze artifacts/performance/process.dmp
```

Useful SOS commands:

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

A GC dump changes process state and has overhead. A process dump is not a substitute for a native profiler when native frames or native heap internals matter.

## Total-memory ownership

Always compare:

- managed live bytes and committed GC heap;
- working set/RSS and private/dirty memory;
- committed/reserved virtual memory;
- native allocator growth;
- mapped files;
- JIT, loader, and executable mappings;
- graphics resources and GPU residency.

Do not assign ownership from one metric.

## Benchmarking and validation

Use BenchmarkDotNet for isolated operations, but never substitute a microbenchmark for an application trace.

A valid report includes equivalent before/after values for relevant metrics:

```text
CPU time / operation
wall-clock latency
throughput
allocation / operation
managed live bytes
working set / RSS
GC pause p95/p99
frame time p95/p99
hitch count
GPU duration
GPU memory/residency
```

Run enough repetitions to expose variance. Report median and a spread measure, not the best run. Check correctness, tail latency, memory lifetime, startup, code size, architecture portability, power, and behavior under contention.
