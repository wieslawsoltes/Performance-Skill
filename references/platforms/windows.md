# Windows profiling with WPR/WPA, PerfView, Visual Studio, WinDbg, PIX, and GPUView

Use this reference for system-wide ETW evidence, native and managed CPU, scheduling, waits, I/O, memory, loader activity, power, Direct3D, presentation, and combined native-managed debugging.

## Environment capture

```powershell
Get-ComputerInfo | Out-File artifacts\performance\windows\computer-info.txt
Get-CimInstance Win32_Processor | Format-List * | Out-File artifacts\performance\windows\cpu.txt
Get-CimInstance Win32_VideoController | Format-List * | Out-File artifacts\performance\windows\gpu.txt
dotnet --info | Out-File artifacts\performance\windows\dotnet-info.txt
wpr -version
wpr -profiles
```

Record Windows build, ADK/WPT version, CPU topology, power plan, GPU/driver, process architecture, elevation, virtualization, and whether the application runs packaged, unpackaged, under a debugger, or through `dotnet.exe`.

```powershell
New-Item -ItemType Directory -Force artifacts\performance\windows | Out-Null
```

## WPR general system trace

```powershell
wpr -start GeneralProfile -filemode
# reproduce deterministic workload
wpr -stop artifacts\performance\windows\general.etl
```

If `GeneralProfile` is not installed, select a suitable profile from `wpr -profiles`. Record the exact profile.

Open in WPA:

```powershell
wpa artifacts\performance\windows\general.etl
```

In WPA first establish the workload time range and exact process lifetime. Framework-dependent applications may appear as `dotnet.exe`; filter by PID, command line, start time, parent process, and image path.

## CPU sampling and precise scheduling

Use a profile that includes sampled CPU and, when needed, context-switch/ready-thread events. Profile names vary by ADK installation.

In WPA inspect:

- CPU Usage (Sampled), grouped by process/thread/stack;
- CPU Usage (Precise), context switches, wait and ready time;
- thread names and priorities;
- DPC/ISR activity;
- hard faults and I/O;
- system-wide competition.

Analysis procedure:

1. select the exact workload interval;
2. filter process and thread;
3. inspect inclusive stack weight;
4. identify whether time is managed, native, kernel, driver, or another process;
5. inspect ready time when latency is high but target CPU is not;
6. inspect wait reason and waker/owner relationships where available;
7. correlate with EventPipe/PerfView for managed names.

High ready time indicates runnable work delayed by CPU saturation, priority, or scheduling—even when the target thread itself is not the top CPU consumer.

## PerfView collection

Bounded collection:

```powershell
PerfView.exe /AcceptEula /NoGui /CollectOnly `
  /CircularMB:1024 `
  /DataFile:artifacts\performance\windows\perfview.etl `
  collect
```

Stop from another elevated terminal:

```powershell
PerfView.exe /AcceptEula /NoGui stop
```

Use current PerfView help for scenario-specific providers and launch options:

```powershell
PerfView.exe /?
```

PerfView is particularly useful for:

- managed CPU stacks and folding;
- GC start/stop, pause, generation, allocation, and promotion;
- sampled allocation stacks;
- contention and ThreadPool events;
- JIT, loader, and module events;
- heap snapshots and retention;
- ETW event correlation.

Keep the raw ETL/ETL.ZIP. Exported reports do not preserve all event detail.

## Visual Studio Profiler

Use Visual Studio Performance Profiler for interactive development scenarios requiring CPU Usage, Instrumentation, Memory Usage, .NET Object Allocation Tracking, File I/O, Database, or UI tools available for the target project type.

Profile a Release/published build without the debugger unless debugger behavior is the subject. Record whether instrumentation or sampling was used because overhead and interpretation differ.

## Symbols

Configure symbols before trusting native stacks:

- Microsoft public symbol server;
- local application PDBs;
- exact native dependency symbols;
- matching binaries and build IDs;
- source indexing/source-link where available.

Use a local symbol cache. Never upload proprietary symbols or dumps to public services unintentionally.

## Native heap and total memory

First correlate:

- process commit/private bytes;
- working set;
- managed live bytes and GC committed heap;
- virtual address mappings;
- native heap allocations;
- mapped files;
- graphics/video memory.

Use WPR heap profiles/providers where installed. Heap tracing can be high overhead and produce large ETLs; keep duration narrow and target the exact process.

For development investigations also consider:

- Visual Studio native memory tools;
- WinDbg heap commands/extensions;
- Application Verifier for misuse/corruption scenarios;
- UMDH/GFlags where appropriate;
- allocator-specific diagnostics.

Do not enable invasive heap instrumentation broadly in production without testing overhead.

## WinDbg and SOS

Use WinDbg when native and managed state must be analyzed together.

Typical setup:

```text
.symfix
.sympath+ <private-symbol-path>
.reload
.loadby sos coreclr
```

Useful native/managed commands depend on architecture and debugger version. Common managed commands include:

```text
!threads
!clrstack
!dumpheap -stat
!gcroot <address>
!syncblk
!finalizequeue
```

For hangs inspect every thread, lock ownership, waits, APCs, loader lock, COM apartments, and UI message pumping. One dump is a snapshot; pair it with repeated stacks or ETW scheduling when progress is uncertain.

## File, disk, registry, and network I/O

Use WPR/WPA tables for:

- file operation count, bytes, duration, path, and stack;
- disk service and queueing;
- hard faults;
- registry activity;
- TCP/IP and networking providers where captured;
- process/thread correlation.

Check antivirus/indexing interference, synchronous I/O on UI/request threads, repeated metadata calls, small fragmented operations, flush frequency, and page-fault-driven startup.

## Loader and startup

For startup traces filter from process start to explicit readiness/first-frame markers. Inspect:

- image/module loads;
- DLL search/probing;
- hard faults and file reads;
- Authenticode/security scanning effects;
- CLR/JIT/ReadyToRun events;
- static initialization;
- window/compositor/device initialization.

Use WPR boot/on-off scenarios only when system boot or logon is actually part of the problem.

## PresentMon

Use PresentMon for independent frame/presentation evidence. Query installed help because CLI syntax evolves:

```powershell
PresentMon.exe --help
```

A common collection shape is:

```powershell
PresentMon.exe `
  --process_id <PID> `
  --timed 30 `
  --output_file artifacts\performance\windows\presentmon.csv
```

Verify options against the installed version. Analyze frame intervals, present mode, display latency fields where available, dropped/missed frames, and process selection.

PresentMon does not identify shader or pass cost. Correlate with PIX/GPUView and application markers.

## GPUView

Use GPUView for system-wide DXGKrnl scheduling and multi-process graphics interference. Capture with the supported WPT/GPUView logging procedure for the installed kit, then inspect:

- contexts, queues, packets, and hardware queues;
- CPU submissions and GPU execution;
- preemption;
- DWM/compositor activity;
- present packets;
- queue starvation and bubbles;
- other processes competing for GPU;
- paging/residency events where present.

GPUView is timeline/scheduling oriented. Use PIX or vendor profilers for detailed API/resource/shader analysis.

## PIX

Use PIX Timing Captures for multi-frame CPU/GPU timelines and PIX GPU Captures for one representative Direct3D 12 frame.

Timing Capture questions:

- which CPU thread prepares/submits work;
- queue depth and idle gaps;
- fence waits;
- overlap between graphics/compute/copy queues;
- frame pacing and present;
- CPU or GPU critical path.

GPU Capture questions:

- event/pass hierarchy;
- command lists and bundles;
- resource state and barriers;
- descriptors/root signatures;
- pipeline state;
- render targets and copies;
- shader timing/counters where supported;
- resource history.

Capture after warm-up unless startup pipeline creation is the subject. Use markers/events in the application.

## Direct3D memory and residency

Track:

- local/nonlocal budget and current usage;
- committed/placed/reserved resources;
- heaps and fragmentation;
- upload/readback heaps;
- transient render targets;
- descriptor heaps;
- deferred release queues;
- evictions and paging;
- integrated versus discrete adapter behavior;
- cross-adapter copies.

Stable process working set does not imply stable video-memory residency, and video-memory allocation does not always appear fully in process private bytes.

## ETW custom instrumentation

Use `EventSource`, `Activity`, or native ETW providers for stable operation/frame markers. Include operation ID, phase, object/document/frame ID, queue, and outcome. Avoid high-cardinality payloads and secrets.

Correlate custom events with PerfView/WPA timelines, runtime events, disk/network, GPU, and present.

## Common Windows misdiagnoses

- a hot `dotnet.exe` process may be the wrong child;
- sampled CPU cannot explain off-CPU delay alone;
- high ready time is not lock wait;
- high GPU engine utilization does not identify the limiting shader or pass;
- DWM queueing can dominate after GPU work completes;
- WARP/software fallback invalidates hardware-GPU assumptions;
- debugger, validation layers, ETW stack walking, and heap tracing can perturb timing;
- working set is not total committed/private/GPU memory.

## Validation

Repeat with the same Windows build, driver, power plan, adapter, display/refresh rate, process architecture, package model, workload, WPR profile, symbol configuration, and capture duration. Report CPU, ready/wait time, I/O, managed/native memory, present/frame metrics, GPU timings, and collection overhead.