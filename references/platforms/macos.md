# macOS profiling with Instruments and `xctrace`

Use this reference for native CPU, scheduling, waits, wakeups, virtual memory, allocations, leaks, filesystem/network activity, Metal, compositor, energy, and driver behavior. Correlate with EventPipe for managed attribution.

## Prerequisites and environment capture

```bash
sw_vers
uname -a
uname -m
xcode-select -p
xcrun xctrace version
system_profiler SPHardwareDataType SPDisplaysDataType
```

Record whether the process is native arm64, x86_64 under Rosetta, sandboxed, hardened, signed, or launched from an app bundle. These affect symbols, process selection, and behavior.

Create an artifact directory:

```bash
mkdir -p artifacts/performance/macos
```

## Discover installed templates and devices

```bash
xcrun xctrace list templates
xcrun xctrace list devices
```

Template names and capabilities vary by Xcode/macOS version. Use the exact installed name and record it.

## Time Profiler: launch

Self-contained executable:

```bash
xcrun xctrace record \
  --template "Time Profiler" \
  --time-limit 30s \
  --output artifacts/performance/macos/cpu.trace \
  --launch -- ./App
```

Framework-dependent executable:

```bash
xcrun xctrace record \
  --template "Time Profiler" \
  --time-limit 30s \
  --output artifacts/performance/macos/cpu.trace \
  --launch -- dotnet exec ./App.dll
```

For an `.app` bundle, launch the actual bundle executable or use Instruments interactively when bundle environment, entitlements, or activation behavior matters.

## Time Profiler: attach

Resolve the exact process:

```bash
pgrep -alf 'App|dotnet'
ps -axo pid,ppid,start,time,%cpu,%mem,command | grep -E 'App|dotnet'
```

Then attach:

```bash
xcrun xctrace record \
  --template "Time Profiler" \
  --attach <PID> \
  --time-limit 30s \
  --output artifacts/performance/macos/cpu.trace
```

Open:

```bash
open artifacts/performance/macos/cpu.trace
```

## Time Profiler analysis procedure

1. select the deterministic workload interval;
2. filter to the exact process and thread;
3. inspect heaviest stack trace by inclusive weight;
4. separate application, CoreCLR, P/Invoke, native library, framework, driver, and kernel frames;
5. inspect thread state and call-tree inversion where useful;
6. compare UI, render, worker, GC, finalizer, and driver-submission threads;
7. correlate managed frames with `dotnet-trace` if JIT symbols are incomplete.

Check:

- sustained CPU versus short spikes;
- spin loops and polling;
- allocator/retain/release traffic;
- CoreCLR JIT/GC/runtime helpers;
- Objective-C messaging overhead;
- lock and syscall boundaries;
- Skia, WebGPU/wgpu-native, Metal, CoreAnimation, CoreGraphics, text/font libraries;
- Rosetta translation or architecture mismatch.

Sampling does not provide exact call counts.

## Scheduling, hangs, and wakeups

Use an installed System Trace–type template for context switches, wakeups, blocking, timers, and system-wide scheduling.

```bash
xcrun xctrace record \
  --template "System Trace" \
  --time-limit 30s \
  --output artifacts/performance/macos/system.trace \
  --attach <PID>
```

If the exact template is unavailable, select the closest installed scheduling/system template interactively.

Inspect:

- runnable versus running time;
- blocking reason and duration;
- wakeup source;
- lock owner/waiter relationships where exposed;
- timer frequency;
- UI main-thread stalls;
- render-thread waits;
- CPU migration and system interference;
- GPU/compositor waits.

High process latency with low sampled CPU often requires this trace rather than more CPU sampling.

## Native allocations

Launch:

```bash
xcrun xctrace record \
  --template "Allocations" \
  --time-limit 60s \
  --output artifacts/performance/macos/allocations.trace \
  --launch -- ./App
```

Attach:

```bash
xcrun xctrace record \
  --template "Allocations" \
  --attach <PID> \
  --time-limit 60s \
  --output artifacts/performance/macos/allocations.trace
```

Use generation marks/snapshots around warm-up and repeated workload. Analyze:

- persistent bytes and object count by allocation stack;
- transient allocation traffic;
- VM allocations versus `malloc` allocations;
- Objective-C/CoreFoundation ownership;
- graphics/native-library allocations;
- resize/reload/retry paths;
- delayed release after queues drain.

Instruments generally sees GC segments and native runtime allocations, not every managed object. Use GC dumps for managed type retention.

## Leaks and ownership

Use the installed Leaks template when native leak detection is appropriate:

```bash
xcrun xctrace record \
  --template "Leaks" \
  --time-limit 60s \
  --output artifacts/performance/macos/leaks.trace \
  --launch -- ./App
```

Treat reported leaks as candidates. Verify application ownership, framework caches, one-time initialization, process shutdown behavior, and whether the allocation remains reachable intentionally.

For Objective-C/CoreFoundation inspect retain/release balance, bridging ownership, autorelease-pool scope, callbacks, blocks/closures, and thread-affine destruction.

## Virtual memory and footprint

Use VM Tracker or the closest installed memory template. Supplement with command-line snapshots:

```bash
vmmap <PID> > artifacts/performance/macos/vmmap.txt
footprint <PID> > artifacts/performance/macos/footprint.txt
ps -o pid,rss,vsz,%mem,command -p <PID>
```

If permitted, repeat `vmmap`/`footprint` at defined workload points.

Distinguish:

- reserved versus committed;
- resident versus nonresident;
- dirty versus clean;
- compressed and swapped;
- anonymous versus file-backed mappings;
- shared versus private;
- CoreCLR GC segments;
- JIT/code mappings;
- Metal heaps/resources;
- mapped assets and caches.

Large virtual reservations are not automatically leaks.

## Filesystem and network

Use installed File Activity and Network templates when latency crosses those boundaries.

Inspect operation count, bytes, latency, synchronous calls on main/render threads, metadata storms, file mapping/page faults, DNS/connect/TLS, socket waits, and interaction with sandbox/container paths.

Correlate timestamps with application `Activity`/EventSource markers.

## Signposts and custom intervals

Add `os_signpost`/Points of Interest through a native shim or supported binding for:

- request/frame begin/end;
- dispatcher queue wait;
- layout/scene generation;
- command encoding;
- native calls;
- upload/readback;
- present;
- cache warm-up.

Use stable names and IDs so Instruments can correlate application intervals with CPU, scheduling, Metal, and VM timelines. Keep instrumentation behind a runtime switch and measure its overhead.

## Metal System Trace

Discover the exact installed template, then launch or attach:

```bash
xcrun xctrace record \
  --template "Metal System Trace" \
  --time-limit 30s \
  --output artifacts/performance/macos/metal-system.trace \
  --launch -- ./App
```

Inspect:

- command-buffer commit, scheduled, start, and completion;
- CPU/GPU overlap;
- queue idle gaps;
- drawable acquisition and starvation;
- render/compute/blit encoders;
- synchronization/events/fences;
- present and compositor timing;
- resource creation and destruction;
- shader/pipeline compilation;
- device utilization, power, and throttling where exposed.

Use a Metal GPU frame capture for API/resource/pipeline/shader analysis of a representative frame. Use the dedicated GPU reference for the full workflow.

## Symbols

For application/native symbols retain:

- exact executable and libraries;
- dSYM bundles;
- build UUIDs;
- matching source commit;
- runtime/native dependency versions.

Verify architecture and UUID match before trusting symbolized stacks. Managed JIT symbolization can remain partial; correlate with EventPipe.

## Export and automation

`xctrace export` can export tables/TOC from trace files. Inspect help and the trace schema for the installed Xcode:

```bash
xcrun xctrace export --help
xcrun xctrace export \
  --input artifacts/performance/macos/cpu.trace \
  --toc > artifacts/performance/macos/cpu-toc.xml
```

Do not hard-code XPath/table assumptions across Xcode versions. Store the raw `.trace` bundle as the source artifact.

## Common macOS misdiagnoses

- hot Metal/framework CPU frames do not prove GPU saturation;
- high RSS does not prove managed retention;
- compressed memory changes footprint interpretation;
- drawable waits may be compositor/vsync pacing, not shader cost;
- one Metal frame capture does not represent long-run pacing;
- Rosetta results are not native-arm64 results;
- debug validation layers and capture mode can substantially perturb timing.

## Validation

Repeat the same workload, process architecture, display, scale factor, refresh rate, power mode, window state, and profiler configuration. Report CPU, waits/wakeups, native persistent bytes, VM footprint, GPU/present timing, and profiler overhead before and after.