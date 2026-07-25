# Linux profiling

Use `perf` for native CPU and hardware counters, eBPF/BCC/bpftrace for low-overhead system-wide and off-CPU evidence, `/proc` for memory ownership, allocator-specific tools for native heaps, and RenderDoc/vendor tools for GPU work.

## CPU sampling

Attach:

```bash
sudo perf record \
  -F 999 \
  -g \
  --call-graph dwarf \
  -p <PID> \
  -o artifacts/performance/linux-perf.data \
  -- sleep 30
```

Launch:

```bash
sudo perf record \
  -F 999 \
  -g \
  --call-graph dwarf \
  -o artifacts/performance/linux-startup.data \
  -- ./App
```

Analyze:

```bash
sudo perf report -i artifacts/performance/linux-perf.data
sudo perf script -i artifacts/performance/linux-perf.data > artifacts/performance/linux-perf.script
```

The best unwind mode depends on frame pointers, DWARF data, binaries, permissions, and overhead. Validate stack quality. Enable the runtime-supported perf-map/perf-jit symbol path for the deployed .NET version; correlate anonymous JIT regions with `dotnet-trace`.

## Scheduler and hardware counters

```bash
pidstat -p <PID> 1
pidstat -t -p <PID> 1
vmstat 1
iostat -xz 1
cat /proc/<PID>/status
cat /proc/<PID>/smaps_rollup
```

```bash
sudo perf stat \
  -p <PID> \
  -e cycles,instructions,cache-misses,branches,branch-misses,context-switches,cpu-migrations,page-faults \
  -- sleep 30
```

Interpret counters relative to the CPU model, virtualization, multiplexing, and cgroup limits.

When available and permitted, use BCC/bpftrace tools such as `profile`, `offcputime`, `runqlat`, `biolatency`, `biosnoop`, networking tools, and allocator probes. Check kernel configuration, BTF, privileges, seccomp, and container capabilities first.

## Memory

Use `/proc/<PID>/smaps_rollup` and detailed `smaps` to distinguish RSS, PSS, private dirty pages, shared mappings, and swap. For native allocations choose a compatible tool:

- heaptrack;
- Valgrind Massif or Memcheck, accepting high overhead;
- jemalloc profiling;
- tcmalloc/pprof;
- reliable eBPF allocation tracing.

Inside containers, dumps and profilers may require `SYS_PTRACE`, relaxed seccomp, host PID visibility, and access to GPU devices. Interpret CPU and memory against cgroup limits, not only host totals.

## GPU and presentation

First prove hardware acceleration and the selected adapter/driver. Detect software paths such as llvmpipe, lavapipe, SwiftShader, WARP-like fallback, or unavailable render nodes.

Use RenderDoc for API-level frame captures of Vulkan/OpenGL and supported applications. Use vendor tooling when available:

- NVIDIA Nsight Graphics/Systems/Compute;
- AMD Radeon GPU Profiler and Radeon Memory Visualizer;
- Intel Graphics Performance Analyzers;
- Mesa/Vulkan driver-specific tracing and counters.

Check:

- Vulkan queue submissions, semaphores, fences, timeline semaphores, events, and pipeline barriers;
- command-buffer reuse and recording cost;
- staging uploads, readbacks, mapping, and flush/invalidate behavior;
- memory heaps, residency, budget, fragmentation, and deferred destruction;
- render-pass/dynamic-rendering attachment load/store operations;
- pipeline and shader compilation during steady state;
- Wayland/X11 compositor queueing, present mode, frame callbacks, and fullscreen behavior;
- PRIME/offload adapter selection and cross-GPU copies;
- GPU frequency/power throttling and thermal state.

A `perf` trace can expose application, loader, ICD, Mesa, Vulkan, OpenGL, and driver CPU overhead, but it does not replace GPU timestamps or hardware-counter analysis.
