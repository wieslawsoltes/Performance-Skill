# Linux profiling with `perf`, `dotnet-trace collect-linux`, eBPF, procfs, allocator tools, and GPU profilers

Use this reference for native and managed CPU, kernel activity, scheduling, off-CPU time, hardware counters, memory ownership, I/O, containers, Vulkan/OpenGL/WebGPU, compositor, and driver behavior.

## Environment capture

```bash
mkdir -p artifacts/performance/linux
uname -a
cat /etc/os-release
lscpu
dotnet --info
perf --version
ldd --version
```

For GPU work also capture:

```bash
lspci -nnk | grep -A3 -E 'VGA|3D|Display'
ls -l /dev/dri
vulkaninfo --summary 2>/dev/null || true
glxinfo -B 2>/dev/null || true
```

Record kernel, libc, CPU, NUMA topology, power governor, container/cgroup limits, process architecture, display server, compositor, GPU, driver, and selected adapter.

## Process discovery

```bash
pgrep -alf 'App|dotnet'
ps -eo pid,ppid,lstart,etime,%cpu,%mem,rss,vsz,cmd | grep -E 'App|dotnet'
```

For framework-dependent apps identify the exact PID, command line, parent process, and lifetime.

## `perf record` CPU sampling

Attach:

```bash
sudo perf record \
  -F 999 \
  -g \
  --call-graph dwarf \
  -p <PID> \
  -o artifacts/performance/linux/cpu.data \
  -- sleep 30
```

Launch:

```bash
sudo perf record \
  -F 999 \
  -g \
  --call-graph dwarf \
  -o artifacts/performance/linux/startup.data \
  -- ./App
```

Analyze:

```bash
sudo perf report -i artifacts/performance/linux/cpu.data
sudo perf script -i artifacts/performance/linux/cpu.data \
  > artifacts/performance/linux/cpu.script
```

The best unwind mode depends on frame pointers, DWARF data, binary stripping, JIT maps, architecture, and overhead. Compare `dwarf`, `fp`, and defaults where necessary. Reject traces dominated by broken or anonymous stacks.

## Managed JIT symbols

Use the runtime-supported perf-map/perf-jit mechanism for the deployed .NET version. Record any environment variables enabled before process start. Verify that managed method names appear correctly in `perf report` before drawing method-level conclusions.

Correlate with `dotnet-trace` when symbol quality is incomplete. Native `perf` sees application/native/runtime/kernel frames; EventPipe is usually better for managed semantic attribution.

## `dotnet-trace collect-linux` on supported .NET/Linux

On supported .NET 10+ systems, `collect-linux` can combine EventPipe with Linux perf events and native/kernel frames. Check support first:

```bash
dotnet-trace collect-linux --probe
```

Requirements include supported runtime/architecture/libc, Linux kernel support for user events, tracefs, and root or required perf capabilities.

Process-specific collection:

```bash
sudo dotnet-trace collect-linux \
  --process-id <PID> \
  --profile dotnet-common,cpu-sampling,thread-time \
  --duration 00:00:00:30 \
  --output artifacts/performance/linux/combined.nettrace
```

For GC-heavy scenarios use an installed/supported GC profile such as `gc-collect` or `gc-verbose` as appropriate. `gc-verbose` can be high volume.

Inspect current help and profiles:

```bash
dotnet-trace collect-linux --help
```

This feature and trace format support evolve. Record tool/runtime versions and verify the analyzer can open the produced trace.

## Hardware counters with `perf stat`

```bash
sudo perf stat \
  -p <PID> \
  -e cycles,instructions,cache-references,cache-misses,branches,branch-misses,context-switches,cpu-migrations,page-faults \
  -- sleep 30
```

Useful derived observations include instructions per cycle, branch-miss rate, cache-miss rate, context-switch rate, and page faults. Interpret relative to CPU model, counter multiplexing, virtualization, frequency scaling, and workload phase.

Use repeated equivalent runs. Counter values from different microarchitectures are not directly interchangeable.

## Scheduler and off-CPU analysis

Basic live evidence:

```bash
pidstat -p <PID> 1
pidstat -t -p <PID> 1
vmstat 1
mpstat -P ALL 1
```

Use `perf sched` where suitable:

```bash
sudo perf sched record -p <PID> -- sleep 30
sudo perf sched timehist
sudo perf sched latency
```

Depending on kernel/tool version, filtering and command syntax vary; inspect `perf sched --help`.

Use BCC/bpftrace off-CPU tools when available:

```bash
sudo offcputime-bpfcc -p <PID> 30 \
  > artifacts/performance/linux/offcpu.txt
sudo runqlat-bpfcc 30 \
  > artifacts/performance/linux/runqlat.txt
```

Command names vary by distribution (`offcputime`, `offcputime-bpfcc`, etc.). Check installed tools.

Correlate:

- on-CPU stacks;
- blocked/off-CPU stacks;
- run-queue delay;
- futex/lock waits;
- I/O waits;
- timer wakeups;
- CPU throttling and migrations.

High latency with low on-CPU samples is usually an off-CPU or queueing question.

## eBPF/BCC/bpftrace tool selection

When installed and permitted:

- `profile`/`profile-bpfcc`: stack sampling;
- `offcputime`: blocked stacks;
- `runqlat`: scheduler queue latency;
- `runqlen`: run-queue depth;
- `biolatency`, `biosnoop`, `biotop`: block I/O;
- `fileslower`, `filetop`, `opensnoop`: file activity;
- `tcpconnect`, `tcpaccept`, `tcplife`, `tcpretrans`: networking;
- `funclatency`: selected native function latency;
- `memleak`: supported native allocation paths.

Check BTF, kernel config, lockdown mode, privileges, seccomp, and container capabilities. Validate stack symbolization and probe safety.

## Procfs memory snapshots

```bash
cat /proc/<PID>/status \
  > artifacts/performance/linux/status.txt
cat /proc/<PID>/smaps_rollup \
  > artifacts/performance/linux/smaps-rollup.txt
cat /proc/<PID>/maps \
  > artifacts/performance/linux/maps.txt
```

For detailed ownership:

```bash
cp /proc/<PID>/smaps artifacts/performance/linux/smaps.txt
```

Interpret:

- RSS and PSS;
- private clean/dirty;
- shared clean/dirty;
- anonymous versus file-backed mappings;
- swap;
- huge pages;
- executable/JIT mappings;
- GC segments;
- native heaps and allocator arenas;
- graphics/driver mappings.

A large VMA is not a leak unless committed/resident/private usage or mapping count grows without bound.

## Native heap: heaptrack

Launch under heaptrack:

```bash
heaptrack ./App
```

Attach where supported by the installed version:

```bash
heaptrack --pid <PID>
```

Analyze with `heaptrack_gui` or command-line tools. Inspect leaked/peak/temporary allocation bytes and allocation stacks. The profiler can add substantial overhead; compare behavior without it.

## Valgrind

Use only for focused native investigations because overhead is high.

```bash
valgrind --tool=massif --massif-out-file=artifacts/performance/linux/massif.out ./App
ms_print artifacts/performance/linux/massif.out \
  > artifacts/performance/linux/massif.txt
```

For memory errors/leaks:

```bash
valgrind --tool=memcheck --leak-check=full ./App
```

Managed/JIT runtimes and native dependencies can produce complex reports. Use suppressions carefully and do not treat every reachable block as a leak.

## Allocator-specific profiling

When the process uses jemalloc or tcmalloc, use their native profiling facilities and exact allocator build/configuration. Verify which allocator owns each allocation; preloading an allocator changes behavior and is an experiment, not a neutral observation.

## File and block I/O

```bash
iostat -xz 1
pidstat -d -p <PID> 1
```

Use eBPF tools for latency and stack correlation. Use `strace` only for narrow syscall questions because it can heavily perturb timing:

```bash
strace -ff -ttT -p <PID> -o artifacts/performance/linux/strace
```

Prefer `perf trace` or eBPF for lower-overhead system-wide analysis where available.

Inspect synchronous calls on hot threads, metadata storms, small fragmented I/O, fsync frequency, page faults, network filesystems, and container overlay filesystems.

## Networking

Use application spans plus OS evidence:

```bash
ss -tinp
sar -n DEV,TCP,ETCP 1
```

Use eBPF networking tools for connections, lifetime, retransmits, and latency where available. Packet capture requires authorization and careful data handling.

## Containers and cgroups

Record:

```bash
cat /proc/<PID>/cgroup
cat /sys/fs/cgroup/cpu.max 2>/dev/null || true
cat /sys/fs/cgroup/cpu.stat 2>/dev/null || true
cat /sys/fs/cgroup/memory.current 2>/dev/null || true
cat /sys/fs/cgroup/memory.peak 2>/dev/null || true
cat /sys/fs/cgroup/memory.max 2>/dev/null || true
cat /sys/fs/cgroup/memory.events 2>/dev/null || true
```

Depending on environment, profiling may require `CAP_PERFMON`, `CAP_SYS_PTRACE`, relaxed seccomp, shared PID namespace, tracefs access, and GPU device mounts. Do not default to privileged containers.

Interpret CPU percentage against quota/cpuset and memory against cgroup limits. Profiler overhead competes inside those limits.

## GPU and presentation discovery

First prove hardware acceleration and adapter selection. Detect llvmpipe, lavapipe, SwiftShader, software OpenGL, wrong PRIME device, missing render-node permissions, or remote-display fallback.

Record environment variables such as `VK_ICD_FILENAMES`, `DRI_PRIME`, vendor offload variables, Wayland/X11 selection, and backend overrides.

## RenderDoc

Use RenderDoc for API-level frame captures of supported Vulkan/OpenGL applications. Launch from the UI or command line supported by the installed version. Capture after warm-up unless pipeline compilation/startup is the subject.

Inspect:

- event/pass hierarchy;
- draw and dispatch calls;
- resource history;
- attachments/load/store;
- pipeline state;
- descriptor sets/bindings;
- barriers and layouts;
- copies and resolves;
- shader inputs/outputs;
- overdraw and mesh/texture inspection.

RenderDoc is not a long-duration scheduler or presentation profiler. Pair it with timestamps, `perf`, compositor traces, and vendor tools.

## Vendor GPU tools

Use the tool matching the actual adapter:

- NVIDIA Nsight Systems for CPU/GPU timeline and system interaction;
- NVIDIA Nsight Graphics for frame/API/shader analysis;
- NVIDIA Nsight Compute for CUDA/compute kernels;
- AMD Radeon GPU Profiler for Vulkan/DX12 queue/wave timing;
- AMD Radeon Memory Visualizer for allocation/residency/fragmentation;
- Intel Graphics Performance Analyzers;
- Mesa/driver-specific tools and counters where supported.

Record tool, driver, firmware, and GPU versions. Counter names and interpretation are architecture-specific.

## Wayland/X11 compositor and present

Identify compositor and session:

```bash
echo "$XDG_SESSION_TYPE"
echo "$WAYLAND_DISPLAY"
echo "$DISPLAY"
ps -ef | grep -E 'kwin|mutter|weston|sway|Xorg|Xwayland'
```

Correlate application frame submission with frame callbacks, present mode, compositor queueing, direct scanout/fullscreen behavior, Xwayland copies, scaling, multiple displays, and refresh-rate mismatch.

A frame can complete on the GPU yet present late because of compositor pacing or callback policy.

## Symbols and build IDs

Retain exact binaries, unstripped symbols/debug packages, build IDs, native dependencies, and source commit. Verify build-ID match before trusting stacks.

Use distribution debuginfo packages and configured symbol/debuginfod services according to policy. Do not publish private symbols.

## Common Linux misdiagnoses

- anonymous JIT frames invalidate managed attribution;
- high system CPU can be driver, futex, page-fault, filesystem, or network work;
- host CPU percentage ignores cgroup quota;
- RSS double-counts shared pages; use PSS/private data;
- software rendering can look like a CPU bottleneck because no hardware GPU is active;
- PRIME/offload can add cross-GPU copies;
- one RenderDoc capture does not explain steady-state frame pacing;
- perf/eBPF privileges and sampling can change behavior.

## Validation

Repeat with the same kernel, libc, runtime, CPU governor, cgroup limits, adapter/driver, display server/compositor, resolution, refresh rate, present mode, workload, symbol setup, and profiler configuration. Report managed/native/kernel CPU, on/off-CPU time, counters, I/O, RSS/PSS/private memory, GPU/present timing, and profiler overhead.