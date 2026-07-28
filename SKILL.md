---
name: dotnet-performance
description: Evidence-first performance engineering workflow for coding agents combining portable .NET diagnostics with platform-native profiling, BenchmarkDotNet, application benchmarking, statistical validation, deployment, container, graphics, and GPU procedures.
---

# .NET Performance Engineering

Use this skill when investigating, explaining, fixing, benchmarking, or validating the performance of a .NET application, including ASP.NET Core, services, console applications, Avalonia, WPF, WinUI, MAUI, Skia, WebGPU, game/graphics engines, NativeAOT, and native-interoperability workloads.

This repository defines one skill. `SKILL.md` is the policy and routing entry point; detailed operational procedures live in a hierarchical reference tree. Load only the indexes and chapters required by the current investigation, then expand when evidence crosses an ownership boundary.

## Non-negotiable rules

- Profile and benchmark an optimized build, normally `Release`, in the real deployment form.
- Record commit and dirty state, SDK/runtime, OS, architecture, hardware, power mode, workload, tool versions, environment overrides, and exact commands.
- Establish a deterministic reproduction before changing code.
- Separate cold startup, first use, warm steady state, overload, drain, and shutdown.
- Warm tiered compilation, shaders, pipelines, caches, and pools unless cold behavior is the subject.
- Collect evidence at every relevant ownership boundary: managed runtime, native library, kernel, scheduler, filesystem/network, dependency, driver, GPU, compositor, and display.
- Do not infer managed retention from RSS alone.
- Do not infer GPU saturation from high frame time, GPU API usage, or utilization alone.
- Do not claim a fix from one average, one trace, one frame capture, one microbenchmark, or the fastest benchmark run.
- Preserve raw artifacts and report missing symbols, dropped events, profiler overhead, environmental variance, and uncertainty.
- Protect secrets and personal data in dumps, traces, logs, SQL spans, packet captures, and benchmark input corpora.
- Treat command examples as version-sensitive. Query installed tool help first; it
  overrides examples when syntax differs. Use
  [`references/command-reference.md`](references/command-reference.md) for verified
  selection rules and canonical forms.[^command-reference]

## Required investigation output

Report:

1. **Symptom** — observable impact and violated target.
2. **Reproduction** — deterministic workload and environment.
3. **Collection** — exact tools, commands, duration, and artifact paths.
4. **Evidence** — counters, traces, captures, dumps, benchmark distributions, and measurements.
5. **Ownership** — managed CPU, runtime, native CPU, kernel, scheduler, I/O, dependency, memory, driver, GPU, compositor, or display.
6. **Dominant cause** — largest supported cost, wait, or fastest-growing resource.
7. **Fix** — smallest high-leverage code or configuration change.
8. **Validation** — equivalent before/after runs with spread and tail metrics.
9. **Residual risks** — unresolved bottlenecks and measurement limits.

Never claim an improvement without before/after evidence from an equivalent workload.

## Reference router

Always begin with [`references/index.md`](references/index.md), [`references/core/index.md`](references/core/index.md), and the verified [`references/command-reference.md`](references/command-reference.md).

Load additional domain indexes by question:

- Managed CPU, allocation, GC, JIT, exceptions, ThreadPool, locks, async stacks, dumps: [`references/runtime/index.md`](references/runtime/index.md)
- Managed/native/VM/mapped/GPU memory ownership and leak analysis: [`references/memory/index.md`](references/memory/index.md)
- Contention, async latency, queues, backpressure, file/network/database I/O, UI dispatcher latency: [`references/latency/index.md`](references/latency/index.md)
- Cold start, first frame/request, loader, JIT, ReadyToRun, trimming, single-file, NativeAOT: [`references/startup/index.md`](references/startup/index.md)
- BenchmarkDotNet, micro/component/macro/load/soak benchmarks, async/concurrency benchmarks, JIT/AOT comparisons, disassembly, hardware counters, statistics, CI gates: [`references/benchmarking/index.md`](references/benchmarking/index.md)
- Production, containers, diagnostic ports, `dotnet-monitor`, triggered collection, Kubernetes, artifact security: [`references/production/index.md`](references/production/index.md)
- UI/rendering/GPU/WebGPU/Metal/D3D/Vulkan/OpenGL/shader/synchronization/presentation: [`references/gpu/index.md`](references/gpu/index.md)

Load every relevant platform reference through [`references/platforms/index.md`](references/platforms/index.md). A single-host investigation usually needs one platform document; cross-platform comparisons and remote/client-server scenarios may require several.

Do not load every document by default. Select the minimum set that answers the current hypothesis, but do not stop at an ownership boundary merely because another guide is required.

## Fast triage sequence

1. Build and run the production-equivalent configuration.
2. Define workload phases, success metrics, and a stopping rule.
3. Record `System.Runtime` counters plus process CPU and total memory.
4. Capture managed CPU/runtime evidence with `dotnet-trace` when managed ownership is plausible.
5. Capture repeated stacks when progress, starvation, or blocking is suspected.
6. If total cost is unexplained, collect the platform-native CPU/scheduler/I/O/memory trace.
7. For memory, compare managed live bytes, GC commitment, private/RSS/PSS, native allocations, mappings, graphics allocations, and GPU residency.
8. For rendering, correlate application markers, CPU submission, GPU timestamps, native GPU capture, present, compositor, and display timing.
9. For benchmark requests, choose micro, component, macro, load, or soak methodology before selecting BenchmarkDotNet or another harness.
10. For production-only incidents, use bounded or triggered collection and record cgroup/host constraints.
11. Implement only after evidence supports the dominant cause.
12. Repeat the identical workload and publish median, spread, tail values, and raw artifacts.

## Ownership tests

- High process CPU with hot managed stacks: application/JIT/runtime work.
- High process CPU below P/Invoke: native library, allocator, graphics API, or driver CPU.
- Low CPU with repeated blocked stacks: synchronization, I/O, scheduler, queueing, or external dependency.
- Rising ThreadPool queue with low CPU and blocking stacks: starvation or sync-over-async.
- Stable managed live bytes with growing private/RSS: native heap, mappings, code heaps, fragmentation, graphics resources, or OS caches.
- Growing live managed graph after equivalent full-collection points: managed retention or intentional unbounded cache.
- Long CPU frame with short GPU timestamps: application/render-thread/driver CPU bound.
- Short CPU submission with long GPU timestamps: GPU execution bound.
- CPU and GPU complete early but present is late: swapchain, compositor, vsync, drawable starvation, or display pacing.
- GPU idle gaps between dependent submissions: CPU starvation, excessive synchronization, serialization, or insufficient buffering.
- High latency with low on-CPU time: off-CPU wait, queueing, dependency, throttling, or scheduler delay.
- Startup improves but first action worsens: work was deferred rather than removed.
- Benchmark improves but the product metric does not: the experiment omitted the critical path, used the wrong input distribution, or optimized a non-dominant operation.

## Agent operating procedure

- Inspect repository build, deployment, diagnostics, benchmark projects, input corpora, CI, and artifact conventions.
- Create `artifacts/performance/<issue-or-timestamp>/` or the repository equivalent.
- Add a deterministic workload driver and stable markers when absent.
- Store commands, environment metadata, analyzer/tool versions, and official reference links beside artifacts.
- Analyze inclusive costs first, then exclusive costs, callees, waits, queueing, synchronization, and ownership.
- Modify code only after the dominant cause is supported.
- Add a benchmark, regression budget, telemetry marker, trace recipe, or lifetime invariant that prevents recurrence.
- Keep large trace, capture, dump, and benchmark artifacts out of Git unless repository policy explicitly stores them.
- Validate failure, cancellation, overload, cleanup, device-loss, and shutdown paths—not only the happy path.

## Invalid conclusions to reject

- “CPU is high, therefore method X is slow” without stacks.
- “RSS grew, therefore the managed heap leaks.”
- “The GC heap is stable, therefore there is no leak.”
- “Average latency/frame time is under budget, therefore tails are healthy.”
- “GPU utilization is high, therefore shader X is the bottleneck.”
- “The render thread is busy, therefore the GPU is busy.”
- “One frame capture represents steady-state behavior.”
- “Fewer draw calls always means faster rendering.”
- “More ThreadPool threads fix starvation.”
- “Async code cannot block.”
- “NativeAOT is automatically faster.”
- “A microbenchmark improvement proves application improvement.”
- “A statistically detectable delta is automatically product-significant.”
- “One benchmark run proves the result.”

## Documentation footnotes

[^command-reference]: [`references/command-reference.md`](references/command-reference.md), which links to the current official documentation for the .NET diagnostic tools, BenchmarkDotNet, Xcode Instruments, Windows Performance Toolkit, Linux `perf`/BCC, PresentMon, RenderDoc, and vendor GPU profilers.
