# Performance Skill

A single, modular coding-agent skill for rigorous cross-platform .NET performance engineering.

The repository exposes one installable skill through [`SKILL.md`](./SKILL.md). Detailed operational procedures are supporting references loaded only when relevant:

```text
SKILL.md
references/
  core-workflow.md
  managed-runtime.md
  memory.md
  concurrency-io-latency.md
  startup-deployment.md
  benchmarking-validation.md
  production-containers.md
  gpu-rendering.md
  macos.md
  windows.md
  linux.md
```

This keeps the skill readable and context-efficient without splitting it into separate skills.

## Coverage

| Area | Operational coverage |
|---|---|
| Managed runtime | `dotnet-counters`, `dotnet-trace`, `dotnet-stack`, `dotnet-gcdump`, `dotnet-dump`, SOS, allocation, GC, JIT, tiering, exceptions, ThreadPool, locks |
| Memory | Managed retention, native heaps, VM mappings, RSS/PSS/private memory, LOH, pinning, finalization, interop ownership, GPU residency |
| Concurrency and latency | Async critical paths, starvation, contention, queues, backpressure, timers, file/network/database I/O, distributed tracing, UI dispatcher latency |
| Startup and deployment | Cold/warm startup, first frame/request, loader, ReadyToRun, trimming, single-file, NativeAOT, first-use regressions |
| .NET benchmarking | BenchmarkDotNet project/configuration, micro/component/macro/load/soak design, async and multithreaded benchmarks, allocations, disassembly, hardware counters, SIMD, JIT/PGO/R2R/AOT comparisons, paired runs, statistical interpretation, CI regression gates, and application validation |
| Production | `dotnet-monitor`, diagnostic ports, containers, Kubernetes, triggered/bounded collection, permissions, privacy and artifact handling |
| macOS | Instruments, `xcrun xctrace`, Time Profiler, System Trace, Allocations, Leaks, VM Tracker, `vmmap`, `footprint`, Metal System Trace |
| Windows | WPR/WPA, ETW, PerfView, Visual Studio Profiler, WinDbg/SOS, native heap tools, PIX, GPUView, PresentMon |
| Linux | `perf`, `dotnet-trace collect-linux`, `perf sched`, eBPF/BCC, procfs, heaptrack, Valgrind, allocator profilers, RenderDoc/vendor GPU tools |
| GPU/rendering | Metal, D3D11/12, Vulkan, OpenGL, WebGPU/wgpu-native, timestamps, queues, barriers, shaders, uploads, memory, compositor and presentation |

## Installation

Copy or link this repository into the skills directory used by your coding agent. A common layout is:

```text
<agent-skills-directory>/dotnet-performance/SKILL.md
```

Keep the `references` directory beside `SKILL.md` so relative links remain valid.

## Intended prompts

```text
Profile this .NET application and find the dominant CPU bottleneck.
```

```text
Investigate why RSS grows while the managed heap stays stable.
```

```text
Diagnose ThreadPool starvation and p99 request latency under load.
```

```text
Compare JIT, ReadyToRun, trimmed single-file, and NativeAOT startup behavior.
```

```text
Create production-grade BenchmarkDotNet benchmarks for this hot path, inspect generated assembly and allocations, and validate the result in the real application.
```

```text
Build a multithreaded benchmark for this queue and measure throughput, p99 latency, fairness, contention, and scaling by worker count.
```

```text
Add stable CI performance regression gates with paired baseline/candidate runs and preserved raw BenchmarkDotNet artifacts.
```

```text
Profile this WebGPU renderer end-to-end and prove whether it is CPU, driver, GPU, compositor, or presentation bound.
```

```text
Collect bounded production evidence from this Kubernetes workload without destabilizing it.
```

```text
Implement the highest-leverage fix and validate it with equivalent before/after traces and benchmarks.
```

## Design principles

- One skill with selectively loaded supporting references.
- Evidence before optimization.
- Portable EventPipe evidence plus OS-native traces.
- Explicit separation of managed, native, kernel, scheduler, I/O, dependency, driver, GPU, compositor, and display costs.
- Exact capture and benchmark commands with analysis procedures, not conceptual checklists alone.
- Reproducible inputs, workloads, and raw artifact preservation.
- Before/after validation using equivalent conditions.
- Tail latency, frame-time distributions, memory slopes, queueing, and benchmark variance—not averages alone.
- Transparent reporting of profiler overhead, symbol quality, permissions, benchmark noise, and uncertainty.

## License

No license file currently exists. Add the intended license before redistributing the skill as a packaged component.