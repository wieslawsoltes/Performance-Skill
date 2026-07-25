---
name: dotnet-performance
summary: Diagnose CPU, memory, allocation, GC, contention, startup, native interop, UI, and GPU performance problems in .NET applications on macOS, Windows, and Linux.
description: A rigorous evidence-first workflow for coding agents. Combines portable .NET EventPipe diagnostics with platform-native profilers: Instruments/xctrace on macOS, WPR/WPA/ETW and PerfView on Windows, and perf/eBPF tooling on Linux.
---

# .NET Performance Engineering Skill

## Mission

Use this skill when a user asks to investigate, measure, explain, reproduce, or improve the performance of a .NET application.

Treat performance work as an experimental discipline. Never optimize from intuition alone when a trace, counter, benchmark, or heap artifact can decide the question.

The objective is not merely to make code look faster. The objective is to:

1. reproduce the problem under controlled conditions;
2. collect evidence at the correct abstraction layers;
3. identify the dominant cost and its ownership boundary;
4. implement the smallest high-leverage fix;
5. prove the improvement without introducing regressions.

This skill applies to:

- .NET, ASP.NET Core, worker services, console applications;
- Avalonia, WPF, WinUI, MAUI, game and graphics applications;
- CoreCLR JIT, ReadyToRun, NativeAOT, Mono, and hybrid native/managed applications;
- CPU, memory, allocations, GC, locks, ThreadPool starvation, startup, I/O, networking, UI responsiveness, rendering, GPU submission, and native interop.

## Non-negotiable rules

- Build and profile an optimized configuration, normally `Release`.
- Record the exact commit, runtime, SDK, OS, architecture, workload, and profiler command.
- Warm up tiered compilation and caches unless startup is the subject.
- Separate startup, steady-state, and shutdown measurements.
- Prefer process launch by the profiler when early startup is relevant.
- Do not infer managed heap retention from RSS alone.
- Do not infer native leaks from managed heap size alone.
- Do not treat one trace as statistically conclusive when variance is material.
- Keep raw artifacts. Never overwrite the only baseline recording.
- Measure before and after with the same workload and environment.
- Report uncertainty, sampling limitations, dropped events, missing symbols, and profiler overhead.

## Required response shape

When reporting an investigation, provide:

1. **Symptom** — observable user or system impact.
2. **Reproduction** — exact workload and commands.
3. **Evidence** — counters, traces, heap data, benchmark results.
4. **Dominant cause** — hottest or fastest-growing path, with ownership boundary.
5. **Fix** — code or configuration change.
6. **Validation** — before/after values and variance.
7. **Residual risks** — remaining bottlenecks and measurement limitations.

Do not claim an improvement without a before/after result.

# Investigation workflow

## Phase 1: establish a controlled workload

Capture:

```text
Repository/commit:
Build configuration:
Target framework:
.NET runtime version:
OS and version:
CPU architecture:
Machine power mode:
Profiler and version:
Input/workload:
Warm-up policy:
Measurement duration:
Run count:
```

Build explicitly:

```bash
dotnet --info
dotnet build -c Release
```

For publish-sensitive scenarios, test the actual deployment model:

```bash
dotnet publish -c Release -r <RID> --self-contained false
```

Use a deterministic workload. For UI applications, describe the interaction sequence precisely: open document, zoom, scroll, resize, animate, switch tabs, or render N frames.

For services, define request rate, concurrency, payload, database state, cache state, and duration.

## Phase 2: first-level portable triage

Install pinned local tools when the repository can contain a tool manifest:

```bash
dotnet new tool-manifest
dotnet tool install dotnet-counters
dotnet tool install dotnet-trace
dotnet tool install dotnet-stack
dotnet tool install dotnet-dump
dotnet tool install dotnet-gcdump
```

On .NET 10 or newer, `dnx` may be used for one-shot execution, but repository-local tools are preferable for reproducibility.

Discover target processes:

```bash
dotnet-counters ps
dotnet-trace ps
dotnet-dump ps
```

Monitor runtime health:

```bash
dotnet-counters monitor \
  --process-id <PID> \
  --counters System.Runtime
```

Collect counters for comparison:

```bash
dotnet-counters collect \
  --process-id <PID> \
  --refresh-interval 1 \
  --format csv \
  --output artifacts/counters-baseline.csv \
  --counters System.Runtime
```

When startup matters, launch through the tool rather than attaching late:

```bash
dotnet-counters collect \
  --format json \
  --output artifacts/startup-counters.json \
  --counters System.Runtime \
  -- dotnet exec ./bin/Release/<TFM>/App.dll
```

Prefer `dotnet exec App.dll` or a self-contained executable over `dotnet run`; `dotnet run` may introduce build activity and child processes that contaminate startup measurements.

### Interpret first-level counters

Correlate, do not inspect metrics in isolation:

- High CPU + low allocation rate: compute, spin, native work, serialization, rendering, or lock contention.
- High allocation rate + frequent Gen 0/1: transient allocation pressure.
- Growing GC heap after full collections: managed retention or cache growth.
- Stable managed heap + growing RSS: native heap, graphics resources, mapped memory, fragmentation, JIT/code heaps, or OS caches.
- High time in GC: allocation volume, promotion, LOH pressure, pinning, or heap-size constraints.
- Growing ThreadPool queue + low CPU: blocking, starvation, sync-over-async, external dependency latency.
- High exception rate: hidden control-flow cost or retry loop.

## Phase 3: portable managed CPU and runtime tracing

Collect a managed CPU sampling trace:

```bash
mkdir -p artifacts

dotnet-trace collect \
  --process-id <PID> \
  --profile cpu-sampling \
  --duration 00:00:30 \
  --format Speedscope \
  --output artifacts/managed-cpu.speedscope.json
```

For startup:

```bash
dotnet-trace collect \
  --profile cpu-sampling \
  --format speedscope \
  --output artifacts/startup.speedscope.json \
  -- dotnet exec ./bin/Release/<TFM>/App.dll
```

For GC and allocation investigations, collect runtime events rather than CPU sampling alone:

```bash
dotnet-trace collect \
  --process-id <PID> \
  --providers Microsoft-Windows-DotNETRuntime:0x1C000080018:5 \
  --duration 00:00:30 \
  --output artifacts/runtime.nettrace
```

Provider masks are scenario-specific. Verify event keywords against the runtime and tool version before relying on a custom mask. Prefer documented profiles when they answer the question.

Capture current managed stacks during hangs or starvation:

```bash
dotnet-stack report --process-id <PID> > artifacts/stacks.txt
```

Use repeated stack snapshots to distinguish a persistent block from a transient sample.

# Memory workflow

## Managed heap

Collect at least two points when investigating growth:

```bash
dotnet-gcdump collect --process-id <PID> --output artifacts/heap-01.gcdump
# Execute the suspect workload repeatedly.
dotnet-gcdump collect --process-id <PID> --output artifacts/heap-02.gcdump
```

Generate portable type statistics where supported:

```bash
dotnet-gcdump report artifacts/heap-01.gcdump > artifacts/heap-01.txt
dotnet-gcdump report artifacts/heap-02.gcdump > artifacts/heap-02.txt
```

A GC dump induces a GC and has nonzero memory/event overhead. Avoid indiscriminate collection in memory-constrained production environments.

For root-path, lock, or comprehensive state analysis, collect a process dump:

```bash
dotnet-dump collect \
  --process-id <PID> \
  --type Full \
  --output artifacts/process.dmp

dotnet-dump analyze artifacts/process.dmp
```

Common SOS commands:

```text
clrthreads
clrstack
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

`dotnet-dump` is managed-state focused; it is not a substitute for a native debugger when native frames and native heap internals are required.

## Native and total process memory

Always compare:

- managed GC heap;
- process working set/RSS;
- private/dirty memory;
- committed virtual memory;
- native heap allocations;
- mapped files;
- graphics and GPU resources;
- JIT, loader, and executable code regions.

If RSS rises while managed live bytes remain stable, move to the platform-native memory profiler.

# macOS: Instruments and `xctrace`

Use Apple Instruments for system-level CPU, scheduling, native allocations, virtual memory, Objective-C/CoreFoundation ownership, Metal, graphics drivers, and native interop.

List installed templates:

```bash
xcrun xctrace list templates
```

## CPU and thread scheduling

Launch a self-contained application:

```bash
xcrun xctrace record \
  --template "Time Profiler" \
  --time-limit 30s \
  --output artifacts/macos-cpu.trace \
  --launch -- ./App
```

Launch a framework-dependent application:

```bash
xcrun xctrace record \
  --template "Time Profiler" \
  --time-limit 30s \
  --output artifacts/macos-cpu.trace \
  --launch -- dotnet exec ./App.dll
```

Attach to an existing process:

```bash
PID=$(pgrep -n App)
xcrun xctrace record \
  --template "Time Profiler" \
  --attach "$PID" \
  --time-limit 30s \
  --output artifacts/macos-cpu.trace
```

Open interactively:

```bash
open artifacts/macos-cpu.trace
```

Inspect:

- per-thread CPU and samples;
- system and kernel transitions;
- blocking, wakeups, and scheduling;
- CoreCLR runtime and JIT-generated regions;
- P/Invoke, Skia, Silk.NET, WebGPU/wgpu-native, Metal, and driver frames.

Managed JIT symbolication may be incomplete. Correlate Instruments with `dotnet-trace`; use Instruments to see the full native/OS stack and EventPipe to identify managed methods.

## Native allocations and virtual memory

Use templates available in the installed Xcode version, typically:

```bash
xcrun xctrace record \
  --template "Allocations" \
  --time-limit 30s \
  --output artifacts/macos-allocations.trace \
  --launch -- ./App
```

Also consider `Leaks`, `VM Tracker`, `System Trace`, `Metal System Trace`, `File Activity`, and `Network` where available.

For .NET applications, Instruments can attribute native `malloc`, VM, Objective-C/CoreFoundation, Metal, mapped-resource, and interop costs. It generally does not expose each managed object allocation as a native allocation. Use a GC dump or managed runtime trace for that layer.

## macOS interpretation

- A hot native frame below a P/Invoke boundary belongs to the native library until proven otherwise.
- High wakeup frequency with low useful CPU often indicates timers, polling, or overly granular rendering invalidation.
- Growing Metal/resource memory with stable managed heap usually requires explicit lifetime/fence/release analysis.
- Large CoreCLR VM reservations are not automatically leaks; distinguish reserved, committed, resident, and dirty pages.

# Windows: WPR/WPA, ETW, PerfView, and Visual Studio

The closest Windows counterpart to Instruments is the Windows Performance Toolkit:

- **WPR** records ETW-based system and application traces.
- **WPA** analyzes CPU sampling, scheduling, I/O, memory, GPU, power, and system-wide timelines.
- **PerfView** provides deep .NET/ETW CPU, allocation, GC, contention, and heap analysis.
- **Visual Studio Profiler** is useful for interactive managed CPU, instrumentation, allocation, and UI investigations.

## WPR/WPA system trace

Start a general recording:

```powershell
New-Item -ItemType Directory -Force artifacts | Out-Null
wpr -start GeneralProfile -filemode
```

Reproduce the workload, then stop:

```powershell
wpr -stop artifacts\windows-general.etl
```

For CPU-focused recording, use an installed WPR profile appropriate to the host:

```powershell
wpr -profiles
wpr -start CPU -filemode
# reproduce
wpr -stop artifacts\windows-cpu.etl
```

Open the ETL in WPA and inspect:

- CPU Usage (Sampled), by process/thread/stack;
- CPU Usage (Precise) and context switches;
- thread wait reasons and ready time;
- disk, file, registry, networking, and hard faults;
- virtual and physical memory;
- GPU utilization and frame/system timelines when providers are present.

Profile names vary by Windows/ADK installation. Query `wpr -profiles`; do not assume every named profile exists.

## PerfView for .NET and ETW

Example command-line collection:

```powershell
PerfView.exe /AcceptEula /NoGui /CollectOnly `
  /CircularMB:1024 `
  /DataFile:artifacts\perfview.etl `
  collect
```

Stop the collection from another terminal:

```powershell
PerfView.exe /AcceptEula /NoGui stop
```

For scripted application launch, use PerfView's documented collection options for the installed version and record the exact command. PerfView is especially strong for:

- managed CPU stacks and folding;
- GC pause and generation analysis;
- allocation stacks and sampled allocations;
- contention and ThreadPool events;
- JIT and module loading;
- heap snapshots and retention paths.

## Windows memory

Use the correct layer:

- managed type growth: GC dump, PerfView heap, Visual Studio Memory Usage;
- native heap: Windows Heap provider, WPR/WPA memory profiles, WinDbg, or Application Verifier as appropriate;
- total commit/working set: WPA memory graphs, Process Explorer, performance counters;
- GPU resources: GPUView/WPA graphics providers and vendor tooling.

For dumps, `dotnet-dump` works cross-platform, while WinDbg with SOS provides combined native and managed debugging on Windows.

## Windows interpretation

- Sampled CPU answers where execution time is spent; precise CPU/context-switch data explains why runnable work is delayed.
- High ready time can indicate CPU saturation even when a target thread itself is not consuming the whole CPU.
- ETW stacks require symbols. Configure Microsoft symbol servers and local symbols, but never publish proprietary PDBs unintentionally.
- A framework-dependent app may appear under `dotnet.exe`; filter by command line, process lifetime, PID, and child process tree.

# Linux: `perf`, eBPF, procfs, and native allocators

The closest general-purpose Linux counterpart to Instruments Time Profiler is `perf`. Combine it with EventPipe because native stack unwinding and managed JIT symbolization have separate constraints.

## CPU sampling with `perf`

Record an existing process:

```bash
sudo perf record \
  -F 999 \
  -g \
  --call-graph dwarf \
  -p <PID> \
  -o artifacts/linux-perf.data \
  -- sleep 30
```

Analyze:

```bash
sudo perf report -i artifacts/linux-perf.data
sudo perf script -i artifacts/linux-perf.data > artifacts/linux-perf.script
```

Launch under `perf`:

```bash
sudo perf record \
  -F 999 \
  -g \
  --call-graph dwarf \
  -o artifacts/linux-startup.data \
  -- ./App
```

The best call-graph mode depends on binaries, kernel permissions, frame pointers, unwind information, and overhead. Compare `dwarf`, `fp`, and platform defaults rather than blindly enforcing one mode.

For managed JIT symbolization, use the runtime-supported perf-map/perf-jit mechanisms for the deployed .NET version. Validate symbol quality before drawing conclusions. A trace dominated by anonymous JIT regions is insufficient for method-level attribution; collect `dotnet-trace` in parallel or sequentially under the same workload.

## Linux system and scheduler evidence

Useful commands:

```bash
pidstat -p <PID> 1
pidstat -t -p <PID> 1
vmstat 1
iostat -xz 1
cat /proc/<PID>/status
cat /proc/<PID>/smaps_rollup
```

Use `perf stat` for hardware and scheduler counters:

```bash
sudo perf stat \
  -p <PID> \
  -e cycles,instructions,cache-misses,branches,branch-misses,context-switches,cpu-migrations,page-faults \
  -- sleep 30
```

Interpret hardware counters carefully across CPU models, virtualization, containers, and multiplexed events.

## eBPF tools

When installed and permitted, use BCC or bpftrace tools for low-overhead, system-wide diagnosis:

- `profile` / `profile-bpfcc` for stack sampling;
- `offcputime` for blocked/off-CPU stacks;
- `runqlat` for scheduler queue latency;
- `biolatency` and `biosnoop` for block I/O;
- `tcpconnect`, `tcplife`, and retransmit tools for networking;
- `memleak` for supported native allocation paths.

Do not assume eBPF availability. Check kernel configuration, privileges, BTF, container capabilities, and security policy.

## Linux memory

Use `/proc/<PID>/smaps_rollup` to distinguish RSS, PSS, private dirty pages, shared mappings, and swap.

For native allocation analysis, select a tool compatible with the allocator and deployment:

- heaptrack;
- Valgrind Massif or Memcheck, accepting substantial overhead;
- jemalloc profiling when the process uses jemalloc;
- tcmalloc/pprof where applicable;
- eBPF native allocation tracing where reliable.

For dumps inside containers, the process/tool may require `SYS_PTRACE` and a compatible seccomp policy.

## Linux interpretation

- High system CPU can indicate syscalls, networking, filesystem, page faults, futex contention, or driver work.
- High off-CPU time often matters more than on-CPU samples for latency problems.
- Container CPU percentages and memory values must be interpreted against cgroup limits, not only host totals.
- RSS includes managed, native, mapped, and shared pages; use PSS/private-dirty data and managed heap evidence before assigning ownership.

# Cross-platform decision matrix

| Question | Portable .NET | macOS | Windows | Linux |
|---|---|---|---|---|
| Which managed method consumes CPU? | `dotnet-trace` | Correlate Instruments | PerfView/VS/ETW | Correlate `perf` |
| Which thread/native library consumes CPU? | Partial | Time Profiler | WPR/WPA | `perf` |
| Why is a thread delayed? | runtime events/stacks | System Trace | WPA precise CPU/waits | `perf sched`, eBPF off-CPU |
| Is GC causing pauses? | counters + runtime trace | Correlate timeline | PerfView/ETW | Correlate timeline |
| Which managed types grow? | `dotnet-gcdump`/dump | same | same + PerfView/VS | same |
| Which native allocations grow? | Not sufficient | Allocations/Leaks | WPR heap/WinDbg/tools | heaptrack/allocator/eBPF |
| Why does RSS grow? | GC heap only | VM Tracker | WPA memory | `/proc/*/smaps*` |
| Is GPU/native rendering expensive? | app events | Metal/Instruments | WPA/GPUView/vendor | vendor tools, `perf`, driver tools |
| Is startup slow? | launch with trace/counters | launch with `xctrace` | WPR/PerfView launch | `perf record -- app` |

# UI and graphics applications

For Avalonia, WPF, WinUI, MAUI, Skia, WebGPU, Metal, Direct3D, Vulkan, and OpenGL workloads, divide every frame into stages:

1. input and dispatcher latency;
2. binding, property propagation, and application logic;
3. layout and measure/arrange;
4. scene generation and invalidation;
5. command encoding and resource uploads;
6. compositor/render-thread work;
7. driver submission;
8. GPU execution;
9. present/vsync and queueing.

Do not call a rendering problem “GPU-bound” merely because it uses a GPU. Prove whether the limiting stage is managed CPU, render-thread CPU, driver CPU, upload bandwidth, GPU execution, synchronization, or presentation.

Collect frame-time distributions rather than averages:

- median;
- p90, p95, p99;
- maximum and hitch count;
- missed-frame percentage against the refresh deadline.

At 60 Hz, the frame budget is approximately 16.67 ms; at 120 Hz, approximately 8.33 ms. Treat these as end-to-end budgets, not CPU-only budgets.

# Benchmarking and validation

Use BenchmarkDotNet for isolated microbenchmarks, but do not substitute a microbenchmark for an application trace.

A valid optimization report includes:

```text
Metric                  Before       After        Delta
CPU time / operation    ...          ...          ...
Wall-clock latency      ...          ...          ...
Allocation / operation  ...          ...          ...
Managed live bytes      ...          ...          ...
Working set / RSS       ...          ...          ...
GC pause p95            ...          ...          ...
Frame time p95          ...          ...          ...
Throughput               ...          ...          ...
```

Run enough repetitions to expose variance. Report median and a spread measure, not only the best run.

Check for regressions in:

- correctness;
- memory lifetime;
- tail latency;
- cold startup;
- code size;
- CPU architecture portability;
- debugability and symbol quality;
- power usage;
- behavior under contention.

# Agent operating procedure

When acting as a coding agent:

1. Inspect repository build, runtime, deployment, and benchmark conventions.
2. Identify whether the request is CPU, latency, memory, startup, I/O, contention, UI, or GPU dominated.
3. Create an `artifacts/performance/<timestamp-or-issue>/` directory or repository-appropriate equivalent.
4. Add a reproducible workload script when absent.
5. Collect portable .NET evidence first unless the symptom is explicitly native/system-level.
6. Collect the platform-native counterpart to establish the complete process/system view.
7. Preserve commands in a `README.md` or investigation note next to artifacts.
8. Analyze the largest inclusive costs first, then exclusive costs and callees.
9. Modify code only after the dominant cause is supported by evidence.
10. Add a benchmark, regression test, telemetry point, or repeatable trace recipe that prevents recurrence.
11. Re-run the same workload and publish before/after evidence.
12. Keep generated profiler binaries and very large traces out of Git unless the repository explicitly stores them; upload them as CI artifacts or release/issue attachments instead.

# Common failure modes

Reject these weak conclusions:

- “CPU is high, therefore method X is slow” without stacks.
- “RSS grew, therefore the managed heap leaks.”
- “The GC heap is stable, therefore there is no leak.”
- “Average frame time is below budget, therefore rendering is smooth.”
- “The profiler shows runtime frames, therefore CoreCLR is the bug.”
- “NativeAOT is automatically faster.”
- “Fewer allocations always means lower latency.”
- “A debug build is representative.”
- “One benchmark run proves the result.”
- “A sampled trace provides exact call counts.”

# References

Prefer primary documentation and record tool versions because commands and profiles evolve:

- .NET diagnostics overview: https://learn.microsoft.com/dotnet/core/diagnostics/
- .NET diagnostic tools: https://learn.microsoft.com/dotnet/core/diagnostics/tools-overview
- `dotnet-counters`: https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-counters
- `dotnet-trace`: https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-trace
- `dotnet-dump`: https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-dump
- `dotnet-gcdump`: https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-gcdump
- Windows Performance Recorder: https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-recorder
- Windows Performance Analyzer: https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-analyzer
- PerfView: https://github.com/microsoft/perfview
- Linux perf documentation: https://perf.wiki.kernel.org/
- BCC tools: https://github.com/iovisor/bcc
- bpftrace: https://github.com/bpftrace/bpftrace
- Apple Instruments and Xcode performance documentation: https://developer.apple.com/documentation/xcode/performance-and-metrics
