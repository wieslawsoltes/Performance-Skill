---
name: dotnet-performance
summary: Diagnose CPU, memory, allocation, GC, contention, startup, native interop, UI, rendering, and GPU performance problems in .NET applications across macOS, Windows, and Linux.
description: Evidence-first performance engineering workflow for coding agents combining portable .NET diagnostics with platform-native CPU, memory, scheduler, graphics, and GPU profilers.
---

# .NET Performance Engineering

Use this skill when investigating or improving the performance of a .NET application, including ASP.NET Core, services, console applications, Avalonia, WPF, WinUI, MAUI, Skia, WebGPU, game engines, and native-interoperability workloads.

This is one skill. Detailed procedures are split into supporting documents to keep the entry point focused. Read only the documents required by the current investigation.

## Core rules

- Profile an optimized build, normally `Release`.
- Record the commit, SDK/runtime, OS, architecture, power mode, workload, profiler version, and exact commands.
- Establish a deterministic reproduction before changing code.
- Separate cold startup, warm steady state, and shutdown.
- Warm tiered compilation, shaders, pipelines, caches, and resource pools unless cold behavior is the subject.
- Collect evidence at every relevant ownership boundary: managed runtime, native library, operating system, graphics API, driver, GPU, compositor, and display.
- Do not infer a managed leak from RSS growth.
- Do not infer GPU saturation from high frame time or GPU API usage.
- Do not optimize from a single average. Use distributions, repeated runs, and before/after evidence.
- Preserve raw traces and report missing symbols, dropped events, profiler overhead, and uncertainty.

## Required investigation output

Report:

1. **Symptom** — observable impact.
2. **Reproduction** — deterministic workload and commands.
3. **Evidence** — counters, traces, captures, dumps, and measurements.
4. **Ownership** — managed CPU, native CPU, kernel, driver, GPU, compositor, I/O, memory, or synchronization.
5. **Dominant cause** — largest supported cost or fastest-growing resource.
6. **Fix** — smallest high-leverage code or configuration change.
7. **Validation** — equivalent before/after runs with variance and tail metrics.
8. **Residual risks** — unresolved bottlenecks and measurement limits.

Never claim an improvement without before/after evidence.

## Workflow router

Start with [`references/core-workflow.md`](references/core-workflow.md) for workload control, portable EventPipe diagnostics, counters, managed CPU, GC, allocation, dumps, benchmarking, and validation.

Then load the platform document matching the target:

- macOS: [`references/macos.md`](references/macos.md)
- Windows: [`references/windows.md`](references/windows.md)
- Linux: [`references/linux.md`](references/linux.md)

For UI, rendering, GPU, WebGPU, Metal, Direct3D, Vulkan, OpenGL, compositor, frame pacing, shader, synchronization, or GPU-memory work, also load:

- [`references/gpu-rendering.md`](references/gpu-rendering.md)

Do not load every reference by default. Select the minimum set needed for the current hypothesis, then expand when evidence crosses an ownership boundary.

## Fast triage

1. Build and run the real deployment configuration.
2. Record `System.Runtime` counters and process CPU/RSS.
3. Capture managed CPU/runtime evidence with `dotnet-trace`.
4. If managed evidence does not explain total cost, collect the platform-native trace.
5. For rendering, correlate application frame markers, CPU submission, GPU timestamps, native GPU capture, present, compositor, and display timing.
6. For memory growth, compare managed live bytes, native allocations, VM mappings, graphics resources, and GPU residency.
7. Implement only after the dominant cost is supported.
8. Repeat the identical workload and report median plus spread and tail values.

## Ownership tests

- High process CPU with hot managed stacks: managed/JIT/application work.
- High process CPU below P/Invoke: native library or driver CPU.
- Low CPU with blocked threads: synchronization, I/O, scheduler, or external dependency.
- Stable managed heap with growing RSS: native heap, mappings, code heaps, graphics resources, fragmentation, or OS caches.
- Long CPU frame with short GPU timestamps: CPU/render-thread bound.
- Short CPU submission with long GPU timestamps: GPU bound.
- Both short but presentation late: queueing, compositor, vsync, drawable/swapchain starvation, or display pacing.
- GPU idle gaps between dependent submissions: CPU starvation, excessive synchronization, serialization, or insufficient buffering.
- High GPU time without unit saturation: dependency stalls, barriers, occupancy limits, bandwidth, cache misses, or poor pass structure.

## Agent operating procedure

- Inspect repository build, deployment, diagnostics, benchmarks, and artifact conventions.
- Create an investigation directory such as `artifacts/performance/<issue-or-timestamp>/`.
- Add a repeatable workload script when none exists.
- Store exact commands and environment metadata beside artifacts.
- Analyze inclusive costs first, then exclusive costs, callees, waits, synchronization, and resource ownership.
- Add a benchmark, regression test, trace recipe, telemetry marker, or frame metric that prevents recurrence.
- Keep large trace/capture binaries out of Git unless repository policy explicitly stores them.

## Common invalid conclusions

Reject claims such as:

- “CPU is high, therefore method X is slow” without stacks.
- “RSS grew, therefore the managed heap leaks.”
- “The GC heap is stable, therefore there is no leak.”
- “Average frame time is under budget, therefore rendering is smooth.”
- “GPU utilization is high, therefore the shader is the bottleneck.”
- “The render thread is busy, therefore the GPU is busy.”
- “One frame capture represents steady-state behavior.”
- “Fewer draw calls always means faster rendering.”
- “NativeAOT is automatically faster.”
- “One benchmark run proves the result.”
