# Benchmarking, experimental design, and performance validation

Use this reference whenever an agent claims a performance improvement, compares implementations, or adds a regression benchmark.

## Choose the correct experiment

Use:

- **microbenchmark** for isolated CPU/allocation cost of a small operation;
- **component benchmark** for parsers, render stages, serializers, allocators, or subsystems with realistic data;
- **application workload** for startup, UI, service throughput, memory lifetime, contention, I/O, rendering, and GPU behavior;
- **production telemetry/capture** when the issue depends on real traffic, topology, hardware, or long-running state.

A microbenchmark cannot prove end-to-end application improvement.

## BenchmarkDotNet baseline

Create a dedicated benchmark project and reference the production project.

```bash
dotnet new console -n Project.Benchmarks
dotnet add Project.Benchmarks package BenchmarkDotNet
dotnet add Project.Benchmarks reference ../Project/Project.csproj
dotnet run -c Release --project Project.Benchmarks
```

Minimal benchmark:

```csharp
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Running;

BenchmarkRunner.Run<HotPathBenchmarks>();

[MemoryDiagnoser]
public class HotPathBenchmarks
{
    private byte[] _input = null!;

    [GlobalSetup]
    public void Setup()
    {
        _input = CreateRepresentativeInput();
    }

    [Benchmark(Baseline = true)]
    public object Baseline() => BaselineImplementation(_input);

    [Benchmark]
    public object Candidate() => CandidateImplementation(_input);

    private static byte[] CreateRepresentativeInput() => new byte[4096];
    private static object BaselineImplementation(byte[] input) => input.Length;
    private static object CandidateImplementation(byte[] input) => input.Length;
}
```

Keep setup outside the measured method unless setup itself is the subject. Consume results when dead-code elimination is possible.

## Benchmark design

Control:

- runtime and target framework;
- architecture;
- deployment model;
- input distributions and sizes;
- culture and globalization mode;
- environment variables;
- CPU affinity/power plan when justified;
- background activity;
- server versus workstation GC;
- tiering and PGO state;
- hardware and firmware;
- thermal state.

Do not silently tune the environment for only one candidate.

## Parameterization

Benchmark realistic regimes, not one convenient size:

```csharp
[Params(16, 256, 4096, 65536)]
public int Size { get; set; }
```

Include adversarial and boundary cases where algorithms change behavior. Avoid huge parameter matrices that make noise and maintenance dominate value.

## Diagnosers

Use only diagnosers needed for the hypothesis. Examples include memory, disassembly, hardware counters, threading, or platform profilers where supported. Diagnosers can change timing and availability varies by OS and privilege.

Run a clean timing benchmark separately when heavy diagnosers perturb the result.

## Statistical interpretation

Report:

- median or mean as appropriate;
- standard deviation and confidence interval where available;
- distribution shape and outliers;
- ratio to baseline;
- allocation bytes and collection counts;
- operation count and total run duration;
- hardware/runtime/job metadata.

Do not report only the fastest iteration. Small deltas near noise require more runs or a better-isolated experiment.

## Equivalence and correctness

Before comparing performance, prove equivalent behavior:

- same output and precision;
- same error handling;
- same ordering and concurrency semantics;
- same caching and lifetime behavior;
- same image quality/render result;
- same validation/security checks;
- same cancellation and timeout behavior.

Optimizations that skip work or weaken semantics are not valid comparisons unless the product requirement changed explicitly.

## Application workload automation

Store a repeatable driver that:

1. starts or attaches to the target;
2. waits for a defined readiness point;
3. performs warm-up;
4. marks measurement begin;
5. executes the exact workload;
6. marks measurement end;
7. requests graceful drain/cleanup;
8. records artifacts and environment metadata.

For UI, automate deterministic input and use stable test data. For services, pin request rate/concurrency and dependency state. For memory, use a fixed operation count and idle/drain window. For GPU, fix resolution, refresh rate, present mode, and adapter.

## Before/after pairing

Prefer paired runs on the same machine under equivalent conditions. Alternate baseline and candidate order when drift or thermal effects matter.

Example sequence:

```text
B A B A B A
```

rather than:

```text
B B B A A A
```

Record run order and exclude runs only with an explicit, predeclared reason.

## Regression thresholds

Use thresholds that reflect noise and product impact. Avoid brittle exact-time assertions in unit tests.

Possible policies:

- statistical benchmark comparison in dedicated CI;
- percentage regression threshold plus absolute floor;
- allocation or object-count budgets;
- startup milestone budget;
- p95/p99 service latency budget;
- frame-time and hitch budget;
- memory-growth slope or plateau budget.

Do not block ordinary CI on noisy microbenchmarks without controlled runners.

## CI benchmark runners

For useful CI comparisons:

- use stable dedicated or isolated runners;
- record CPU model, OS image, runtime, power settings, and tool versions;
- avoid co-tenancy where possible;
- preserve raw benchmark output;
- compare against a known baseline commit;
- separate correctness tests from performance jobs;
- treat virtualization and cloud frequency scaling as sources of variance.

When dedicated hardware is unavailable, use CI for large regressions and trend tracking, not tiny deltas.

## Profiling-guided optimization loop

1. establish a failing product metric;
2. collect a representative trace;
3. identify dominant inclusive cost or wait;
4. create a focused benchmark only if it reproduces that cost;
5. implement one coherent change;
6. rerun benchmark and application workload;
7. collect a second trace to prove ownership moved or disappeared;
8. verify no new bottleneck dominates.

A benchmark improvement without a corresponding application improvement may mean the benchmark omitted the real critical path.

## Performance report template

```text
Environment
  Commit/runtime/OS/architecture/hardware/power mode:
  Deployment and profiler versions:

Workload
  Input, warm-up, duration, concurrency, run count:

Metric                     Before       After        Delta        Spread
Wall-clock latency         ...          ...          ...          ...
CPU time                    ...          ...          ...          ...
Throughput                  ...          ...          ...          ...
Allocation/op               ...          ...          ...          ...
Managed live bytes          ...          ...          ...          ...
Private/RSS                 ...          ...          ...          ...
GC pause p95/p99            ...          ...          ...          ...
Queue wait p95/p99          ...          ...          ...          ...
Frame time p95/p99          ...          ...          ...          ...
GPU duration                ...          ...          ...          ...
GPU memory/residency        ...          ...          ...          ...
Errors/timeouts/hitches     ...          ...          ...          ...
```

Explain causality using traces, not only metric correlation.

## Final validation checklist

Check:

- functional correctness;
- tail latency;
- throughput at target and overload;
- allocation and GC;
- managed/native/GPU memory lifetime;
- startup and first-use latency;
- code size and publish size;
- multiple architectures and adapters;
- thermal/power behavior;
- diagnostics and debuggability;
- cancellation, failure, and recovery paths.

A complete optimization report states what did not improve and any residual measurement uncertainty.