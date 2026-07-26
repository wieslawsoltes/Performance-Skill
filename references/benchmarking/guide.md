# .NET benchmarking, experimental design, and performance validation

Use this reference whenever an agent compares implementations, claims a performance improvement, introduces a regression benchmark, evaluates runtimes or deployment models, or converts profiler evidence into a repeatable experiment.

The goal is not to produce a pretty BenchmarkDotNet table. The goal is to build an experiment that answers a concrete engineering question without measuring setup noise, dead code, different semantics, thermal drift, or a workload that no longer resembles the application.

# 1. Choose the correct experiment

Use:

- **microbenchmark** for isolated CPU, allocation, branch, vectorization, parsing, formatting, lookup, or synchronization cost of a small operation;
- **component benchmark** for parsers, serializers, render stages, schedulers, caches, allocators, protocol handlers, or subsystems with realistic state and data;
- **macrobenchmark** for process startup, CLI commands, compiler passes, document loading, request pipelines, UI interactions, render loops, and end-to-end scenarios;
- **load benchmark** for throughput, concurrency, queueing, tail latency, backpressure, database, networking, or service saturation;
- **soak benchmark** for memory lifetime, fragmentation, cache growth, handle/resource leaks, thermal behavior, and long-running stability;
- **production telemetry or capture** when the issue depends on real traffic shape, topology, hardware, deployment constraints, user behavior, or state that cannot be reconstructed safely in a benchmark.

A microbenchmark cannot prove an end-to-end application improvement. A macrobenchmark can prove product impact but may not identify the responsible method. Use both when necessary.

## Decision table

| Question | Preferred experiment |
|---|---|
| Which implementation is faster for one operation? | Microbenchmark |
| Which parser scales better across realistic files? | Component benchmark |
| Did startup improve? | Process-level macrobenchmark |
| Did service throughput improve under load? | Load benchmark |
| Does memory plateau after repeated use? | Soak benchmark |
| Did a shader optimization improve frame pacing? | Application/GPU benchmark plus capture |
| Does NativeAOT improve this deployment? | Equivalent published-artifact macrobenchmark |
| Is a production regression workload-specific? | Production trace plus reproduced component/application benchmark |

# 2. Benchmark prerequisites

Before writing code, record:

```text
Question being answered:
Primary metric:
Secondary/regression metrics:
Baseline implementation or commit:
Candidate implementation or commit:
Required semantic equivalence:
Representative input source:
Expected operating ranges:
Target runtime(s):
Target architecture(s):
Deployment model(s):
Machine and power policy:
Run count and stopping rule:
Acceptable regression threshold:
```

Do not start from “make this method faster.” Start from a measurable product or subsystem symptom and identify the operation that owns it using profiling evidence.

# 3. BenchmarkDotNet project setup

Create a dedicated executable project. Do not place serious benchmarks in the production application or unit-test process.

```bash
dotnet new console -n Project.Benchmarks
dotnet add Project.Benchmarks package BenchmarkDotNet
dotnet add Project.Benchmarks reference ../Project/Project.csproj
```

Recommended project file:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net10.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <AllowUnsafeBlocks>true</AllowUnsafeBlocks>
    <IsPackable>false</IsPackable>
    <Optimize>true</Optimize>
  </PropertyGroup>

  <ItemGroup>
    <PackageReference Include="BenchmarkDotNet" Version="*" />
    <ProjectReference Include="../Project/Project.csproj" />
  </ItemGroup>
</Project>
```

Pin package versions in a real repository through central package management, a lock file, or repository conventions. Do not leave `Version="*"` in committed production code.

Program entry point:

```csharp
using BenchmarkDotNet.Running;

BenchmarkSwitcher
    .FromAssembly(typeof(Program).Assembly)
    .Run(args);
```

Run explicitly in Release:

```bash
dotnet run -c Release --project Project.Benchmarks -- --list flat
dotnet run -c Release --project Project.Benchmarks -- --filter '*HotPath*'
```

Prefer `BenchmarkSwitcher` over hardcoding one benchmark class so CI and local workflows can select categories and filters.

# 4. Minimal correct benchmark

```csharp
using BenchmarkDotNet.Attributes;

[MemoryDiagnoser]
public class HotPathBenchmarks
{
    private byte[] _input = null!;

    [GlobalSetup]
    public void GlobalSetup()
    {
        _input = CreateRepresentativeInput();
    }

    [Benchmark(Baseline = true)]
    public int Baseline() => BaselineImplementation(_input);

    [Benchmark]
    public int Candidate() => CandidateImplementation(_input);

    private static byte[] CreateRepresentativeInput() => new byte[4096];

    private static int BaselineImplementation(byte[] input) => input.Length;

    private static int CandidateImplementation(byte[] input) => input.Length;
}
```

Rules:

- keep input construction, file loading, service startup, and unrelated setup outside the measured method;
- include setup in the measured method only when setup is part of the product operation;
- return or consume outputs so the JIT cannot remove work;
- avoid logging, assertions, console output, tracing, and debugger attachment in measured code;
- do not share mutable state between invocations unless that state is intentionally part of the workload;
- ensure the benchmark operation reaches the same semantic result for baseline and candidate.

# 5. Lifecycle and state isolation

BenchmarkDotNet lifecycle hooks:

```csharp
[GlobalSetup]
public void GlobalSetup() { }

[GlobalCleanup]
public void GlobalCleanup() { }

[IterationSetup]
public void IterationSetup() { }

[IterationCleanup]
public void IterationCleanup() { }
```

Use `GlobalSetup` for immutable or reusable state. Use `IterationSetup` only when every measurement iteration requires a fresh state and the setup cost must remain outside timing.

Heavy iteration setup can distort process state, caches, GC, or branch predictors even when not included directly in the reported operation time. Prefer benchmark designs that reset minimal state.

## Invocation versus operation

If one benchmark invocation performs multiple logical operations, declare the count:

```csharp
[Benchmark(OperationsPerInvoke = 1024)]
public int Batch()
{
    var sum = 0;
    for (var i = 0; i < 1024; i++)
    {
        sum += Work(i);
    }

    return sum;
}
```

Do not use batching merely to hide timer resolution unless the operation is genuinely too short and the framework cannot produce stable measurements. BenchmarkDotNet already performs repeated invocation internally.

# 6. Parameterization and realistic inputs

Use parameters for regimes where algorithmic behavior changes:

```csharp
[Params(16, 256, 4096, 65536)]
public int Size { get; set; }
```

Use `ParamsSource` for structured cases:

```csharp
public IEnumerable<TestCase> Cases()
{
    yield return new("SmallAscii", CreateAscii(64));
    yield return new("LargeUtf8", CreateUtf8(64 * 1024));
    yield return new("Pathological", CreatePathologicalInput());
}

[ParamsSource(nameof(Cases))]
public TestCase Case { get; set; } = null!;
```

Include:

- typical inputs;
- boundary sizes;
- empty and minimal cases;
- large but realistic cases;
- adversarial cases where complexity or allocation behavior changes;
- hot-cache and cold-cache variants when both matter;
- successful and failure paths when both occur in production.

Do not benchmark only random data unless production data is random. Randomness can defeat realistic branch prediction and cache locality.

When using random data:

- use a fixed seed;
- generate data outside measured code unless generation is part of the workload;
- preserve the generated corpus as an artifact when reproducibility matters.

# 7. Avoiding invalid benchmarks

## Dead-code elimination

Return values or use `BenchmarkDotNet.Engines.Consumer`:

```csharp
using BenchmarkDotNet.Engines;

private readonly Consumer _consumer = new();

[Benchmark]
public void ConsumeResult()
{
    _consumer.Consume(Compute());
}
```

Do not replace a realistic consumer with an artificial volatile write unless you understand its cost and memory-ordering effects.

## Constant folding and precomputation

Avoid constants that allow compile-time or JIT-time folding:

```csharp
private int _value;

[GlobalSetup]
public void Setup() => _value = Environment.TickCount & 1023;

[Benchmark]
public int Compute() => Expensive(_value);
```

Inspect disassembly when results are unexpectedly close to zero or a candidate appears impossibly fast.

## Accidental allocation omission

If the product operation returns or stores an object, do not benchmark only an internal span-based core that avoids the required materialization.

## Different semantics

Verify:

- exact or acceptable numerical precision;
- error and exception behavior;
- ordering;
- thread safety;
- cancellation;
- validation/security checks;
- allocation ownership and disposal;
- cache state;
- output/image quality;
- deterministic versus nondeterministic behavior.

An optimization that skips required work is not a valid candidate.

## Benchmarking wrappers instead of work

A benchmark dominated by delegate invocation, reflection, DI resolution, serialization setup, test framework wrappers, or process startup may be valid only if those costs are part of the product path. Otherwise isolate them.

# 8. Baselines, ratios, and categories

Use one semantically valid baseline per comparison group:

```csharp
[Benchmark(Baseline = true)]
public int Current() => CurrentImplementation(_input);

[Benchmark]
public int Proposed() => ProposedImplementation(_input);
```

Use categories to separate fast PR benchmarks from long nightly suites:

```csharp
[BenchmarkCategory("Parsing", "PR")]
[Benchmark]
public int ParseSmall() => Parse(_small);

[BenchmarkCategory("Parsing", "Nightly")]
[Benchmark]
public int ParseLarge() => Parse(_large);
```

Run:

```bash
dotnet run -c Release --project Project.Benchmarks -- --anyCategories PR
dotnet run -c Release --project Project.Benchmarks -- --allCategories Parsing Nightly
```

Do not compare ratios across unrelated benchmark classes, jobs, machines, or environments.

# 9. Jobs and runtime configuration

Use jobs to compare runtimes, JIT modes, GC modes, architecture, environment variables, or deployment settings.

Example custom configuration:

```csharp
using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Environments;
using BenchmarkDotNet.Jobs;
using BenchmarkDotNet.Running;

var config = ManualConfig
    .Create(DefaultConfig.Instance)
    .AddJob(Job.Default
        .WithId("Default")
        .WithRuntime(CoreRuntime.Core100))
    .AddJob(Job.Default
        .WithId("ServerGC")
        .WithRuntime(CoreRuntime.Core100)
        .WithEnvironmentVariable("DOTNET_gcServer", "1"));

BenchmarkSwitcher
    .FromAssembly(typeof(Program).Assembly)
    .Run(args, config);
```

Verify actual BenchmarkDotNet API names against the pinned package version. Runtime constants and toolchain APIs evolve.

Useful dimensions:

- target framework/runtime version;
- x64 versus Arm64;
- workstation versus server GC;
- concurrent GC settings;
- tiered compilation on/off;
- dynamic PGO on/off;
- ReadyToRun on/off;
- invariant globalization versus full globalization;
- feature flags or algorithm switches;
- hardware intrinsics enabled/disabled for diagnosis;
- NativeAOT versus CoreCLR only when using appropriate toolchains and equivalent published behavior.

Do not construct a giant Cartesian product. Each job must answer a hypothesis.

# 10. JIT, tiering, and PGO

Modern .NET performance depends on tiered compilation and dynamic PGO. BenchmarkDotNet normally handles warm-up, but the agent must still understand what is being measured.

Record:

- runtime version;
- tiered compilation state;
- dynamic PGO state;
- ReadyToRun state;
- warm-up count and duration;
- whether first-tier, optimized-tier, or mixed behavior is relevant.

For steady-state throughput, allow the benchmark to reach optimized code. For startup and first-use latency, do not use a warmed microbenchmark as evidence; use a process-level benchmark.

Diagnostic comparisons may use environment variables such as runtime tiering/PGO controls, but exact variables and support must be checked against the target runtime version. Do not cargo-cult old COMPlus or DOTNET settings.

A candidate that improves Tier 1 code while worsening startup or Tier 0 may still regress interactive applications.

# 11. ReadyToRun, single-file, trimming, and NativeAOT

Benchmark deployment models using published artifacts rather than only BenchmarkDotNet’s default generated process.

For example:

```bash
dotnet publish src/App/App.csproj -c Release -r osx-arm64 -o artifacts/publish/framework-dependent

dotnet publish src/App/App.csproj -c Release -r osx-arm64 \
  -p:PublishReadyToRun=true \
  -o artifacts/publish/r2r

dotnet publish src/App/App.csproj -c Release -r osx-arm64 \
  -p:PublishAot=true \
  -o artifacts/publish/aot
```

Then use a process-level harness to measure:

- process launch to readiness;
- first request or first frame;
- steady-state throughput;
- private memory/RSS;
- binary and publish size;
- CPU architecture behavior;
- reflection/dynamic-code compatibility;
- diagnostics and symbolization.

Do not compare NativeAOT and CoreCLR using a microbenchmark alone and generalize to deployment. NativeAOT can change startup, code size, steady-state optimization, diagnostics, and feature compatibility in different directions.

# 12. Memory and allocation benchmarking

Use `[MemoryDiagnoser]` for managed allocation per operation:

```csharp
[MemoryDiagnoser]
public class AllocationBenchmarks
{
    [Benchmark(Baseline = true)]
    public string Baseline() => BuildBaseline();

    [Benchmark]
    public string Candidate() => BuildCandidate();
}
```

Interpret:

- allocated bytes/op;
- Gen 0/1/2 collection counts;
- operation throughput;
- retained versus transient allocations;
- pooling side effects;
- large-object behavior;
- finalization or native wrapper ownership.

BenchmarkDotNet’s memory diagnoser does not prove absence of:

- native allocations;
- pinned memory;
- unmanaged buffers;
- GPU allocations;
- cache retention;
- process lifetime growth;
- fragmentation;
- allocation bursts outside the measured operation.

For those, combine the benchmark with EventPipe, platform native allocation tools, dumps, or a soak workload.

## Pooling benchmarks

When comparing pooling:

- include pool warm-up separately;
- measure steady-state reuse;
- test pool exhaustion and contention;
- test retained memory after idle;
- ensure returned objects are reset correctly;
- include realistic size distributions;
- verify that lower allocations do not increase latency or memory footprint.

# 13. Disassembly and code-generation analysis

Use disassembly when the question involves:

- inlining;
- bounds-check elimination;
- devirtualization;
- vectorization;
- hardware intrinsics;
- register spills;
- code size;
- loop unrolling;
- unexpected helper calls;
- tiering differences.

Example:

```csharp
using BenchmarkDotNet.Attributes;
using BenchmarkDotNet.Diagnosers;

[DisassemblyDiagnoser(
    printSource: true,
    maxDepth: 3,
    exportCombinedDisassemblyReport: true)]
public class CodegenBenchmarks
{
    [Benchmark]
    public int Sum() => SumImplementation(_data);

    private int[] _data = Enumerable.Range(0, 1024).ToArray();
}
```

Run disassembly separately from the clean timing run because diagnosers can perturb execution.

Check:

- whether the expected method was inlined;
- whether the benchmark body collapsed to a constant;
- whether interface or virtual dispatch remains;
- whether vector instructions match the target ISA;
- whether bounds checks remain in the hot loop;
- whether helper calls allocate or throw;
- code-size growth and instruction-cache implications.

Do not judge code solely by instruction count. A shorter sequence may have worse dependencies, throughput, latency, cache behavior, or branch predictability.

# 14. Hardware counters

Hardware counters can answer whether a CPU benchmark is limited by:

- instructions and cycles;
- branch misses;
- cache misses;
- frontend/backend stalls;
- memory bandwidth;
- vectorization effectiveness.

Availability depends on OS, CPU, permissions, hypervisor, and BenchmarkDotNet diagnoser support.

Rules:

- verify that counters are supported on the host;
- record multiplexing or scaling;
- compare only equivalent hardware and counter configurations;
- separate counter runs from clean timing runs;
- do not compare raw counts across different operation counts;
- prefer normalized metrics such as instructions/op, cycles/op, branch misses/op, and cache misses/op;
- interpret counters in the context of generated code and application behavior.

On Linux, `perf stat` can complement BenchmarkDotNet:

```bash
perf stat -r 10 \
  -e cycles,instructions,branches,branch-misses,cache-references,cache-misses \
  dotnet run -c Release --project Project.Benchmarks -- --filter '*Target*'
```

This wraps the whole benchmark process, including harness overhead, so use it mainly for diagnostic comparisons or isolate the generated benchmark executable when appropriate.

# 15. Async benchmarks

BenchmarkDotNet supports `Task` and `ValueTask` return types:

```csharp
[MemoryDiagnoser]
public class AsyncBenchmarks
{
    private Service _service = null!;

    [GlobalSetup]
    public void Setup() => _service = CreateService();

    [Benchmark(Baseline = true)]
    public Task<Result> Baseline() => _service.BaselineAsync();

    [Benchmark]
    public ValueTask<Result> Candidate() => _service.CandidateAsync();
}
```

Avoid:

- `.Result`, `.Wait()`, or `GetAwaiter().GetResult()` unless sync-over-async is the subject;
- benchmarking only completed tasks when production usually performs real asynchronous work;
- including network or disk variance in a microbenchmark unless testing an integration component;
- reusing mutable async state unsafely;
- ignoring cancellation and exception paths.

For I/O-heavy async operations, a macro/load benchmark is usually more meaningful than nanosecond-level BenchmarkDotNet timing.

# 16. Multithreaded and contention benchmarks

Single-thread microbenchmarks cannot prove scalability.

For lock-free structures, queues, caches, schedulers, and pools, measure:

- throughput versus thread count;
- p50/p95/p99 operation latency;
- fairness and starvation;
- failed retries/CAS loops;
- allocation per operation;
- CPU utilization;
- cache-line contention and false sharing;
- behavior under read/write mixes;
- behavior at saturation and overload.

BenchmarkDotNet’s standard benchmark method is not itself a full load generator. For many concurrent scenarios, build a dedicated harness that:

1. creates worker threads/tasks;
2. synchronizes their start;
3. runs for a fixed duration or operation count;
4. records per-worker counts and latency histograms;
5. stops cleanly;
6. reports aggregate throughput and distribution;
7. repeats across concurrency levels.

Do not use `Parallel.For` inside a benchmark and interpret only mean operation time without understanding scheduler and harness overhead.

## False-sharing diagnosis

When throughput collapses with thread count:

- inspect cache-line placement;
- separate frequently written counters;
- use hardware counters where available;
- compare affinity/topology behavior;
- validate on more than one CPU architecture.

# 17. SIMD and hardware-intrinsic benchmarks

When benchmarking vectorized implementations:

- verify actual ISA support on the host;
- record `Vector128/256/512` and architecture expectations;
- inspect disassembly;
- test small sizes where scalar setup dominates;
- test misalignment and tail handling;
- test realistic memory alignment and stride;
- compare bandwidth-limited and compute-limited regimes;
- ensure scalar and vector results are numerically equivalent.

Do not publish AVX-512 or architecture-specific results as general .NET performance without identifying the machine and fallback behavior.

# 18. Collections, LINQ, spans, and source generators

For collection and API benchmarks, include realistic usage patterns:

- cold creation versus repeated reuse;
- enumeration only versus materialization;
- known-size versus unknown-size input;
- interface dispatch versus concrete types;
- value-type versus reference-type elements;
- comparer costs;
- hashing collisions;
- mutation and resizing;
- exceptions and misses.

For LINQ comparisons, preserve semantics such as deferred execution, ordering, multiple enumeration, and allocation ownership.

For source-generator or generated-code comparisons, benchmark the generated runtime behavior and also measure build-time and generated-code-size impacts when relevant.

# 19. Serialization and parsing benchmarks

Use representative payload corpora rather than one toy object.

Measure separately:

- serialization and deserialization;
- validation;
- UTF-8 encode/decode;
- buffer allocation and pooling;
- stream versus span/pipe APIs;
- successful and malformed input;
- small-message latency and large-message throughput;
- source-generated versus reflection metadata paths;
- cold metadata initialization versus steady state.

Record payload bytes and report throughput such as MB/s in addition to time/op.

# 20. Database, network, and service benchmarks

Do not use BenchmarkDotNet alone for realistic remote I/O.

Use a load tool or custom harness and control:

- client and server machines;
- connection pooling;
- warm connections;
- DNS and TLS state;
- request rate versus closed-loop concurrency;
- payload distribution;
- database state and indexes;
- cache state;
- dependency latency;
- retries and timeouts;
- target and overload phases.

Report:

- requests/second;
- p50/p90/p95/p99/max latency;
- errors and timeouts;
- queue depth;
- CPU and allocation rate;
- GC pauses;
- network and storage utilization;
- database wait categories;
- saturation point.

A throughput increase caused by unbounded queueing is not an improvement.

# 21. UI, rendering, and GPU benchmarks

Use a deterministic application harness rather than a microbenchmark for frame pacing.

Fix:

- window size and scaling;
- display refresh rate;
- adapter and driver;
- present mode;
- test scene/document;
- camera/zoom state;
- animation time source;
- warm-up frames;
- measurement frame count;
- compositor/window visibility state.

Measure:

- end-to-end frame p50/p90/p95/p99/max;
- missed-frame percentage;
- hitch count;
- update/layout/render CPU time;
- GPU timestamps per pass;
- uploads/readbacks;
- resource and residency growth;
- image correctness and quality.

Use the GPU profiling reference for native captures and queue/shader analysis. A BenchmarkDotNet benchmark of command encoding may help isolate CPU cost but cannot prove end-to-end smoothness.

# 22. Process-level startup benchmark harness

For startup, execute published artifacts in fresh processes.

A harness should:

1. prepare cold or warm state explicitly;
2. launch the exact executable;
3. record a monotonic start timestamp;
4. wait for a defined readiness signal;
5. record first request/first frame/ready timestamp;
6. terminate gracefully;
7. repeat enough times;
8. alternate baseline and candidate;
9. record failures and timeouts.

Use a readiness signal stronger than “process exists,” such as:

- IPC message;
- HTTP readiness endpoint;
- first rendered-frame marker;
- application event;
- expected output file or socket.

Do not use `dotnet run` for startup benchmarks because build and CLI overhead contaminate the measurement.

# 23. Benchmark configuration examples

## Config with explicit summary style and exporters

```csharp
using BenchmarkDotNet.Columns;
using BenchmarkDotNet.Configs;
using BenchmarkDotNet.Exporters;
using BenchmarkDotNet.Loggers;

public sealed class BenchmarkConfig : ManualConfig
{
    public BenchmarkConfig()
    {
        AddLogger(ConsoleLogger.Default);
        AddExporter(MarkdownExporter.GitHub);
        AddExporter(JsonExporter.Full);
        AddColumnProvider(DefaultColumnProviders.Instance);

        WithOptions(ConfigOptions.JoinSummary);
    }
}
```

Apply:

```csharp
[Config(typeof(BenchmarkConfig))]
public class HotPathBenchmarks
{
}
```

Verify API availability against the repository’s pinned BenchmarkDotNet version.

## Environment metadata

Store alongside results:

```bash
dotnet --info > BenchmarkDotNet.Artifacts/dotnet-info.txt
uname -a > BenchmarkDotNet.Artifacts/uname.txt 2>/dev/null || true
```

On Windows also capture OS build, CPU model, and power plan. On macOS capture hardware model and power mode. On Linux capture governor, cgroup limits, and virtualization/container metadata.

# 24. Running benchmarks correctly

Recommended local workflow:

```bash
dotnet restore
dotnet build -c Release --no-restore
dotnet run -c Release --no-build --project Project.Benchmarks -- \
  --filter '*ParserBenchmarks*' \
  --exporters json markdown
```

Useful BenchmarkDotNet CLI options vary by version. Use:

```bash
dotnet run -c Release --project Project.Benchmarks -- --help
```

Do not assume every option exists in every pinned version.

Rules:

- close unnecessary applications;
- connect laptops to stable power;
- avoid thermal throttling;
- use a stable power plan/governor;
- avoid debugger attachment;
- run baseline and candidate on the same machine;
- avoid comparing results captured after unrelated SDK, BIOS, OS, or firmware updates without noting the change;
- preserve the entire artifact directory, not only copied table rows.

# 25. Statistical interpretation

BenchmarkDotNet reports estimates and distribution data, but the agent must still decide whether the effect is meaningful.

Report:

- mean and/or median;
- error/confidence interval;
- standard deviation;
- ratio to baseline;
- allocation bytes/op;
- collection counts;
- sample count;
- outliers and distribution shape;
- hardware/runtime/job metadata.

Do not report only the fastest iteration.

## Practical significance

A statistically detectable 0.5% change may have no product value. A noisy 15% tail-latency regression may be critical even when the mean is unchanged.

Define thresholds using both:

- **relative change**, such as 5%;
- **absolute floor**, such as 50 ns, 1 ms, 1 MB, or 0.5% missed frames.

This prevents tiny operations from failing on meaningless relative changes and large operations from hiding important absolute regressions.

## Noise diagnosis

When results are unstable, investigate:

- thermal throttling;
- CPU frequency scaling;
- background processes;
- virtualization/co-tenancy;
- NUMA placement;
- GC mode;
- input mutation;
- hidden I/O;
- timer resolution;
- benchmark duration;
- branch/cache state;
- process affinity;
- antivirus/indexing;
- JIT tier transitions.

Do not simply increase iteration count until the desired conclusion appears.

# 26. Before/after pairing

Prefer paired runs on the same machine under equivalent conditions. Alternate order to reduce drift:

```text
B A B A B A
```

rather than:

```text
B B B A A A
```

For commit comparisons:

1. create clean worktrees or published artifacts for baseline and candidate;
2. ensure identical SDK selection and package restore state;
3. build both before measurement;
4. alternate executions;
5. preserve raw artifacts separately;
6. record commit SHAs and dirty state;
7. exclude runs only by a predeclared rule.

# 27. CI benchmarking

Use dedicated or isolated runners when benchmarks gate merges.

Capture:

- CPU model and topology;
- RAM;
- OS image/kernel;
- runtime/SDK;
- BenchmarkDotNet version;
- power policy;
- virtualization/container state;
- repository commit;
- baseline commit;
- raw artifacts.

Recommended tiers:

- **PR smoke benchmarks**: short, coarse thresholds, detect major regressions;
- **nightly benchmarks**: broader parameter sets and runtimes;
- **scheduled dedicated-hardware benchmarks**: small deltas, hardware counters, stable trend history;
- **release benchmarks**: deployment/startup/throughput/memory across supported platforms.

Do not block ordinary shared-runner CI on 1–2% timing changes.

## Example GitHub Actions skeleton

```yaml
name: Benchmarks

on:
  workflow_dispatch:
  schedule:
    - cron: '0 2 * * *'

jobs:
  benchmark:
    runs-on: [self-hosted, performance]
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '10.0.x'

      - run: dotnet restore
      - run: dotnet build -c Release --no-restore
      - run: >-
          dotnet run -c Release --no-build
          --project Project.Benchmarks
          -- --anyCategories Nightly

      - uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: BenchmarkDotNet.Artifacts/**
```

Pin action versions and SDKs according to repository policy. Prefer immutable action SHAs in security-sensitive repositories.

# 28. Regression gates

Possible policies:

- percentage regression plus absolute threshold;
- allocation budget per operation;
- zero-allocation requirement for a hot path;
- startup milestone budget;
- throughput floor;
- p95/p99 latency ceiling;
- frame-time and hitch budget;
- memory-growth slope or plateau requirement;
- publish-size budget;
- code-size budget from disassembly.

A gate should:

- use stable hardware;
- compare equivalent configurations;
- tolerate known noise;
- produce actionable artifacts;
- distinguish warning from failure;
- allow explicit review for intentional tradeoffs.

Do not encode performance assertions as ordinary unit tests using `Stopwatch` and fixed millisecond limits.

# 29. Profiling-guided optimization loop

1. establish a failing product metric;
2. collect a representative trace;
3. identify the dominant inclusive cost, wait, allocation, or resource owner;
4. create a focused benchmark that reproduces the relevant cost;
5. verify benchmark semantics and generated code;
6. implement one coherent change;
7. rerun benchmark under identical conditions;
8. rerun the application workload;
9. collect a second trace to prove ownership moved or disappeared;
10. verify that no new bottleneck or regression dominates.

A benchmark improvement without application improvement usually means:

- the benchmark omitted the critical path;
- the optimized operation was not dominant;
- another stage became the bottleneck;
- setup, I/O, synchronization, or memory lifetime dominates;
- the workload distribution is wrong;
- the optimization regressed tail behavior or another platform.

# 30. Repository organization

Recommended layout:

```text
benchmarks/
  Project.Benchmarks/
    Project.Benchmarks.csproj
    Program.cs
    Benchmarks/
    Inputs/
    Config/
    README.md
artifacts/
  performance/
    <date-or-issue>/
```

Benchmark README should document:

- what each suite measures;
- required datasets;
- supported platforms;
- expected run duration;
- categories;
- local commands;
- CI commands;
- known sources of noise;
- baseline policy;
- artifact locations.

Do not commit large generated BenchmarkDotNet artifact directories unless repository policy requires it. Upload them as CI artifacts or attach them to performance investigations.

# 31. Agent implementation procedure

When adding benchmarks to a repository:

1. inspect target frameworks, SDK pinning, package management, CI, and existing benchmark conventions;
2. identify the product symptom and profiling evidence;
3. choose micro, component, macro, load, or soak methodology;
4. add a dedicated benchmark project or extend the existing one;
5. use representative and boundary inputs;
6. implement baseline and candidate with equivalent semantics;
7. add only hypothesis-relevant jobs and diagnosers;
8. run a clean timing benchmark;
9. run diagnostic passes separately when needed;
10. inspect warnings, generated code, and result distributions;
11. preserve raw artifacts;
12. rerun the corresponding application workload;
13. document commands and interpretation;
14. add CI execution only when runner stability and thresholds are appropriate.

# 32. Performance report template

```text
Question
  What decision does this benchmark support?

Environment
  Commit(s):
  Dirty state:
  SDK/runtime:
  BenchmarkDotNet:
  OS/kernel:
  CPU/architecture/topology:
  RAM:
  Power/governor:
  Virtualization/container:
  Deployment model:

Benchmark design
  Type: micro/component/macro/load/soak
  Input corpus and distributions:
  Parameters:
  Setup and cleanup:
  Jobs/runtime settings:
  Diagnosers:
  Warm-up and measurement policy:
  Run order:

Correctness
  Output equivalence:
  Error/cancellation semantics:
  Lifetime/disposal equivalence:

Results
  Metric                     Baseline      Candidate     Delta       Spread
  Mean/median                ...           ...           ...         ...
  p95/p99                    ...           ...           ...         ...
  Throughput                 ...           ...           ...         ...
  Allocation/op              ...           ...           ...         ...
  Gen0/1/2                   ...           ...           ...         ...
  Instructions/op            ...           ...           ...         ...
  Cycles/op                  ...           ...           ...         ...
  Code size                  ...           ...           ...         ...
  Startup/readiness          ...           ...           ...         ...
  RSS/private memory         ...           ...           ...         ...
  Errors/timeouts/hitches    ...           ...           ...         ...

Application validation
  Corresponding product metric before/after:
  Trace/capture evidence:

Conclusion
  Practical significance:
  Tradeoffs:
  Residual uncertainty:
  Recommended action:
```

# 33. Final checklist

Before accepting a benchmark result, verify:

- Release build was used;
- no debugger was attached;
- benchmark and production target the intended runtime and architecture;
- setup is correctly included or excluded;
- outputs prevent dead-code elimination;
- baseline and candidate are semantically equivalent;
- inputs are representative and reproducible;
- warm-up matches the question;
- runtime tiering/PGO state is understood;
- allocations are interpreted correctly;
- heavy diagnosers were separated from clean timing;
- distributions and uncertainty were inspected;
- result is practically meaningful;
- paired before/after runs used equivalent conditions;
- application-level validation was performed;
- raw artifacts and metadata were preserved;
- remaining tradeoffs and uncertainty were reported.

A complete optimization report states not only what became faster, but also what did not improve, what regressed, which environments were tested, and why the benchmark represents the real workload.