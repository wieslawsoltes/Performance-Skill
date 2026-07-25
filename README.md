# Performance Skill

Coding-agent skills for rigorous, cross-platform .NET performance engineering.

The repository combines managed runtime diagnostics with each operating system's native performance stack:

| Layer | macOS | Windows | Linux |
|---|---|---|---|
| Managed runtime | `dotnet-counters`, `dotnet-trace`, `dotnet-stack`, `dotnet-gcdump`, `dotnet-dump` | Same | Same |
| Native/system CPU | Instruments / `xcrun xctrace` | WPR/WPA, ETW, PerfView | `perf`, eBPF |
| Native memory | Instruments Allocations, Leaks, VM Tracker | WPA heap/memory, WinDbg, PerfView | heaptrack, allocator profilers, `/proc`, eBPF |
| Scheduling and waits | Instruments System Trace | WPA precise CPU and wait analysis | `perf sched`, off-CPU eBPF tools |
| Graphics/GPU | Metal System Trace, Metal Debugger, GPU counters | WPR/WPA, PIX, GPUView, PresentMon | RenderDoc and vendor profilers |
| Vendor GPU analysis | Apple Metal tools | PIX, NVIDIA Nsight, AMD RGP, Intel GPA | NVIDIA Nsight, AMD RGP, Intel GPA |

## Skill files

### General .NET performance

[`SKILL.md`](./SKILL.md) contains the complete cross-platform workflow for:

- CPU and native CPU profiling;
- managed and native memory analysis;
- allocation and GC investigations;
- thread scheduling, contention, startup, I/O, and UI responsiveness;
- initial graphics and GPU classification;
- repeatable before/after validation.

### GPU performance

[`gpu-performance/SKILL.md`](./gpu-performance/SKILL.md) is the dedicated GPU companion skill for:

- Metal, Direct3D 11/12, Vulkan, OpenGL, and WebGPU;
- Avalonia, Skia, WPF, WinUI, MAUI, and custom .NET renderers;
- CPU/GPU frame decomposition and frame-pacing analysis;
- application markers and asynchronous GPU timestamp queries;
- Metal Debugger, GPU captures, Metal counters, and `xctrace`;
- WPR/WPA, PIX, GPUView, PresentMon, DXGI, DWM, and video-memory analysis;
- RenderDoc, NVIDIA Nsight Graphics, AMD Radeon GPU Profiler, and Intel GPA;
- shader occupancy, divergence, bandwidth, cache, and stall analysis;
- queue synchronization, barriers, uploads, residency, and resource lifetime;
- WebGPU/wgpu-native backend correlation;
- p50/p95/p99 frame, GPU-pass, presentation, hitch, and missed-deadline validation.

The GPU skill references the general skill and expects agents to combine managed, native, driver, compositor, and GPU evidence instead of diagnosing from GPU utilization alone.

## Installation

Copy or link this repository into the skills directory used by your coding agent. The exact location depends on the agent host.

A common layout is:

```text
<agent-skills-directory>/dotnet-performance/SKILL.md
<agent-skills-directory>/dotnet-performance/gpu-performance/SKILL.md
```

The skills do not require helper binaries from this repository and can be applied to an existing .NET codebase without changing that codebase first. For serious graphics investigations, the GPU skill may direct the agent to add low-overhead semantic markers and asynchronous timestamp-query instrumentation to the target application.

## Intended prompts

Examples:

```text
Profile this .NET application and find the dominant CPU bottleneck.
```

```text
Investigate why RSS keeps growing while the managed heap appears stable.
```

```text
Compare Avalonia rendering performance on macOS, Windows, and Linux.
```

```text
Determine whether this WebGPU renderer is CPU-bound, driver-bound, GPU-bound, or presentation-bound.
```

```text
Capture Metal, D3D12, and Vulkan frame evidence, identify the dominant pass or synchronization bubble, implement the highest-leverage fix, and validate it.
```

```text
Profile shader, upload, queue, residency, and presentation costs and report p50/p95/p99 frame-time improvements.
```

## Design principles

- Evidence before optimization.
- Portable EventPipe evidence plus OS-native traces.
- Explicit separation of managed, native, kernel, driver, compositor, and GPU costs.
- GPU timestamps and profiler captures before assigning pass or shader cost.
- Reproducible workloads and exact profiler commands.
- Before/after validation using the same environment.
- Tail latency and frame-time distributions, not averages alone.
- Raw trace preservation and transparent reporting of profiler limitations.
- Final validation outside replay, capture, validation-layer, and hardware-counter modes.

## License

No license file has been added by this change. Add the repository's intended license before redistributing the skills as packaged components.
