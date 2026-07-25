# Windows profiling

Use Windows Performance Recorder/Analyzer for system-wide ETW evidence, PerfView for deep .NET analysis, PIX and GPUView for graphics, PresentMon for presentation timing, and WinDbg/SOS for combined native-managed dumps.

## WPR/WPA

Discover installed profiles:

```powershell
wpr -profiles
```

General recording:

```powershell
New-Item -ItemType Directory -Force artifacts\performance | Out-Null
wpr -start GeneralProfile -filemode
# reproduce workload
wpr -stop artifacts\performance\windows-general.etl
```

CPU-focused profiles vary by ADK installation; query rather than assuming a name.

In WPA inspect sampled CPU, precise CPU/context switches, ready time, wait reasons, disk/file/network activity, hard faults, commit/working set, GPU engines, DXGKrnl events, and present timelines when providers are present.

High ready time can indicate CPU saturation even when the target thread is not consuming the entire CPU. Configure symbols and filter framework-dependent apps by PID, command line, lifetime, and process tree because they may appear as `dotnet.exe`.

## PerfView and managed ETW

Example collection:

```powershell
PerfView.exe /AcceptEula /NoGui /CollectOnly `
  /CircularMB:1024 `
  /DataFile:artifacts\performance\perfview.etl `
  collect
```

Stop from another terminal:

```powershell
PerfView.exe /AcceptEula /NoGui stop
```

Use PerfView for managed CPU stacks, GC pauses, sampled allocations, contention, ThreadPool activity, JIT/module loading, and heap retention. Use current tool documentation for scenario-specific command options.

## Native and total memory

Select the ownership layer:

- managed type growth: GC dump, PerfView heap, Visual Studio Memory Usage;
- native heap: WPR heap providers, WPA, WinDbg, Application Verifier, allocator-specific tooling;
- commit/working set: WPA memory graphs, Process Explorer, counters;
- graphics resources: DXGI budgets, PIX, WPA/GPUView, vendor tools.

Use WinDbg with SOS when native and managed state must be inspected together.

## Direct3D and presentation

Use PIX Timing Captures to correlate CPU threads, queue submissions, GPU execution, synchronization, and frame pacing over time. Use a PIX GPU Capture for one representative D3D12 frame to inspect command lists, events, barriers, descriptors, pipeline state, resources, render targets, and shaders.

Use GPUView for system-wide DXGKrnl scheduling, contexts, queues, packets, preemption, DWM/compositor activity, and multi-process interference. Use PresentMon for independent presentation-mode and frame-interval evidence.

Check:

- render-thread versus GPU critical path;
- command-list recording and queue submission overhead;
- queue idle gaps and CPU starvation;
- fence waits, cross-queue synchronization, bubbles, and serialization;
- transition/UAV/aliasing barriers and ownership changes;
- descriptor heap pressure and descriptor rebinding;
- upload/readback heaps and copies;
- PSO/shader creation during steady state;
- resource residency, budget pressure, evictions, and paging;
- DXGI present mode, waitable swapchain behavior, DWM queueing, tearing/vsync, and latency;
- integrated versus discrete adapter selection and cross-adapter copies.

Do not diagnose a shader from GPU utilization alone. Use PIX or vendor counters to identify the limiting stage, occupancy, bandwidth, cache behavior, divergence, register pressure, or fixed-function bottleneck.
