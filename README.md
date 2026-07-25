# Performance Skill

A coding-agent skill for rigorous, cross-platform .NET performance engineering.

The skill combines managed runtime diagnostics with each operating system's native performance stack:

| Layer | macOS | Windows | Linux |
|---|---|---|---|
| Managed runtime | `dotnet-counters`, `dotnet-trace`, `dotnet-stack`, `dotnet-gcdump`, `dotnet-dump` | Same | Same |
| Native/system CPU | Instruments / `xcrun xctrace` | WPR/WPA, ETW, PerfView | `perf`, eBPF |
| Native memory | Instruments Allocations, Leaks, VM Tracker | WPA heap/memory, WinDbg, PerfView | heaptrack, allocator profilers, `/proc`, eBPF |
| Scheduling and waits | Instruments System Trace | WPA precise CPU and wait analysis | `perf sched`, off-CPU eBPF tools |
| Graphics/GPU | Metal System Trace and Instruments | WPA/GPUView/vendor profilers | vendor profilers, driver tools, `perf` |

## Skill file

The complete agent instructions are in [`SKILL.md`](./SKILL.md).

## Installation

Copy or link this repository into the skills directory used by your coding agent. The exact location depends on the agent host.

A common layout is:

```text
<agent-skills-directory>/dotnet-performance/SKILL.md
```

The skill is intentionally self-contained. It does not require scripts from this repository and can be applied to an existing .NET codebase without changing that codebase first.

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
Capture startup, steady-state, and frame-time evidence, implement the highest-leverage fix, and validate it.
```

## Design principles

- Evidence before optimization.
- Portable EventPipe evidence plus OS-native traces.
- Explicit separation of managed, native, kernel, driver, and GPU costs.
- Reproducible workloads and exact profiler commands.
- Before/after validation using the same environment.
- Tail latency and frame-time distributions, not averages alone.
- Raw trace preservation and transparent reporting of profiler limitations.

## License

No license file has been added by this change. Add the repository's intended license before redistributing the skill as a packaged component.
