# Performance Skill

A single, modular coding-agent skill for rigorous cross-platform .NET performance engineering.

The repository exposes one installable skill through [`SKILL.md`](./SKILL.md). Detailed procedures are organized by domain and platform:

```text
SKILL.md
references/
  core/
    index.md
    guide.md
  runtime/
    index.md
    guide.md
  memory/
    index.md
    guide.md
  latency/
    index.md
    guide.md
  startup/
    index.md
    guide.md
  benchmarking/
    index.md
    guide.md
  production/
    index.md
    guide.md
  gpu/
    index.md
    guide.md
  platforms/
    index.md
    macos.md
    windows.md
    linux.md
```

Each `index.md` is a compact router. The corresponding `guide.md` preserves the complete operational content, while the platform directory groups native tooling in one place. This keeps the skill readable and context-efficient without creating multiple skills.

## Coverage

| Area | Operational coverage |
|---|---|
| Managed runtime | `dotnet-counters`, `dotnet-trace`, `dotnet-stack`, `dotnet-gcdump`, `dotnet-dump`, SOS, allocation, GC, JIT, tiering, exceptions, ThreadPool, locks |
| Memory | Managed retention, native heaps, VM mappings, RSS/PSS/private memory, LOH, pinning, finalization, interop ownership, GPU residency |
| Concurrency and latency | Async critical paths, starvation, contention, queues, backpressure, timers, file/network/database I/O, distributed tracing, UI dispatcher latency |
| Startup and deployment | Cold/warm startup, first frame/request, loader, ReadyToRun, trimming, single-file, NativeAOT, first-use regressions |
| .NET benchmarking | BenchmarkDotNet configuration, micro/component/macro/load/soak design, async and multithreaded benchmarks, allocations, disassembly, hardware counters, SIMD, JIT/PGO/R2R/AOT comparisons, paired runs, statistical interpretation, CI regression gates, and application validation |
| Production | `dotnet-monitor`, diagnostic ports, containers, Kubernetes, triggered/bounded collection, permissions, privacy, and artifact handling |
| Platform tooling | Instruments/`xctrace`; WPR/WPA, ETW, PerfView, WinDbg; `perf`, eBPF, procfs, native allocators |
| GPU/rendering | Metal, D3D11/12, Vulkan, OpenGL, WebGPU/wgpu-native, timestamps, queues, barriers, shaders, uploads, memory, compositor, and presentation |

## Installation

Copy or link this repository into the skills directory used by your coding agent:

```text
<agent-skills-directory>/dotnet-performance/SKILL.md
```

Keep the complete `references` directory beside `SKILL.md` so relative links remain valid.

## Example prompts

```text
Profile this .NET application and find the dominant CPU bottleneck.
```

```text
Investigate why RSS grows while the managed heap stays stable.
```

```text
Create production-grade BenchmarkDotNet benchmarks for this hot path, inspect generated assembly and allocations, and validate the result in the real application.
```

```text
Profile this WebGPU renderer end-to-end and prove whether it is CPU, driver, GPU, compositor, or presentation bound.
```

```text
Collect bounded production evidence from this Kubernetes workload without destabilizing it.
```

## Design principles

- One skill with selectively loaded domain and platform references.
- Evidence before optimization.
- Exact capture and benchmark commands with analysis procedures.
- Explicit ownership across managed, native, kernel, scheduler, I/O, driver, GPU, compositor, and display layers.
- Reproducible inputs, workloads, and raw artifact preservation.
- Equivalent before/after validation with tail metrics and variance.

## License

No license file currently exists. Add the intended license before redistributing the skill as a packaged component.
