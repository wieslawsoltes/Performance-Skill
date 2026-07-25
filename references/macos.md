# macOS profiling

Use Instruments and `xcrun xctrace` for native CPU, scheduling, virtual memory, allocations, CoreFoundation/Objective-C ownership, Metal, compositor, and driver activity. Correlate with EventPipe for managed attribution.

## Discover templates

```bash
xcrun xctrace list templates
```

Template names vary by Xcode version. Query the installed templates instead of assuming availability.

## CPU and scheduling

```bash
xcrun xctrace record \
  --template "Time Profiler" \
  --time-limit 30s \
  --output artifacts/performance/macos-cpu.trace \
  --launch -- ./App
```

Framework-dependent application:

```bash
xcrun xctrace record \
  --template "Time Profiler" \
  --time-limit 30s \
  --output artifacts/performance/macos-cpu.trace \
  --launch -- dotnet exec ./App.dll
```

Attach:

```bash
PID=$(pgrep -n App)
xcrun xctrace record \
  --template "Time Profiler" \
  --attach "$PID" \
  --time-limit 30s \
  --output artifacts/performance/macos-cpu.trace
```

Open:

```bash
open artifacts/performance/macos-cpu.trace
```

Inspect per-thread samples, wakeups, context switches, blocking, kernel transitions, CoreCLR/JIT regions, P/Invoke boundaries, native libraries, graphics frameworks, and drivers. Managed JIT symbols may be incomplete; use `dotnet-trace` for managed names and Instruments for the complete native/system stack.

## Native memory

```bash
xcrun xctrace record \
  --template "Allocations" \
  --time-limit 30s \
  --output artifacts/performance/macos-allocations.trace \
  --launch -- ./App
```

Also consider installed templates such as Leaks, VM Tracker, System Trace, File Activity, Network, and Metal System Trace.

Distinguish reserved, committed, resident, dirty, compressed, and swapped memory. Large CoreCLR reservations are not automatically leaks. Stable managed live bytes with growing native/Metal memory requires resource-lifetime, heap, mapping, drawable, and fence analysis.

## Metal and presentation

Use Metal System Trace for system-wide queue, command-buffer, CPU/GPU overlap, synchronization, and presentation timelines. Use a Metal GPU capture for one representative frame to inspect encoders, resources, pipeline state, shader execution, counters, and pass structure.

Capture after warm-up unless cold shader/pipeline creation is the subject. Add debug labels and signposts around frame stages, command buffers, passes, uploads, and presents.

Check:

- drawable acquisition latency and drawable starvation;
- command-buffer commit-to-start and start-to-end intervals;
- CPU/GPU overlap and queue idle gaps;
- render/compute/blit encoder boundaries;
- load/store actions and unnecessary attachment preservation;
- memoryless/tile-local opportunities on Apple GPUs;
- storage modes and avoidable synchronization/copies;
- resource creation or shader compilation during steady state;
- retained drawables, command buffers, textures, heaps, and deferred releases;
- compositor and vsync timing versus actual GPU completion.

Do not equate high process CPU in Metal/framework frames with GPU execution. Driver submission can be CPU-bound while the GPU remains underutilized.
