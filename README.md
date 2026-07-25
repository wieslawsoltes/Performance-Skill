# Performance Skill

A single, modular coding-agent skill for rigorous cross-platform .NET performance engineering.

The repository exposes one installable skill through [`SKILL.md`](./SKILL.md). Detailed procedures are supporting references loaded by the agent only when relevant:

```text
SKILL.md
references/
  core-workflow.md
  macos.md
  windows.md
  linux.md
  gpu-rendering.md
```

This keeps the skill readable and context-efficient without splitting it into separate skills.

## Coverage

| Layer | macOS | Windows | Linux |
|---|---|---|---|
| Managed runtime | `dotnet-counters`, `dotnet-trace`, `dotnet-stack`, `dotnet-gcdump`, `dotnet-dump` | Same | Same |
| Native/system CPU | Instruments / `xcrun xctrace` | WPR/WPA, ETW, PerfView | `perf`, eBPF |
| Native memory | Instruments Allocations, Leaks, VM Tracker | WPA heap/memory, WinDbg, PerfView | heaptrack, allocator profilers, `/proc`, eBPF |
| Scheduling and waits | Instruments System Trace | WPA precise CPU and wait analysis | `perf sched`, off-CPU eBPF tools |
| Graphics/GPU | Metal Debugger, Metal System Trace, GPU counters | PIX, GPUView, WPA, PresentMon, vendor tools | RenderDoc, Nsight, RGP, Intel GPA, Vulkan tooling |
| APIs/frameworks | Metal, WebGPU, Skia, Avalonia | D3D11/12, DXGI, WebGPU, WPF, WinUI, Avalonia | Vulkan, OpenGL, WebGPU, Wayland/X11, Avalonia |

## Installation

Copy or link this repository into the skills directory used by the coding agent. A common layout is:

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
Profile this WebGPU renderer end-to-end and prove whether it is CPU, driver, GPU, compositor, or presentation bound.
```

```text
Compare Avalonia frame pacing and GPU memory behavior on macOS, Windows, and Linux.
```

```text
Capture startup, steady-state, and frame-time evidence, implement the highest-leverage fix, and validate it.
```

## Design principles

- One skill with selectively loaded supporting references.
- Evidence before optimization.
- Portable EventPipe evidence plus OS-native traces.
- Explicit separation of managed, native, kernel, driver, GPU, compositor, and display costs.
- Reproducible workloads and exact profiler commands.
- Before/after validation using equivalent conditions.
- Tail latency and frame-time distributions, not averages alone.
- Raw artifact preservation and transparent profiler limitations.

## License

No license file currently exists. Add the intended license before redistributing the skill as a packaged component.
