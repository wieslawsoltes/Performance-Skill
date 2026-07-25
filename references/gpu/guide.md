# GPU and rendering performance

Use this reference together with the target platform document. This is an operational profiling playbook, not only a conceptual checklist. The goal is to prove which stage owns latency, throughput loss, memory growth, power consumption, or frame instability.

# Non-negotiable GPU rules

- Never call a workload GPU-bound merely because it uses a GPU.
- Record the adapter, driver, backend API, resolution, refresh rate, presentation mode, power mode, and display topology.
- Capture CPU and GPU timelines for the same deterministic workload.
- Add stable debug labels and timestamp ranges before drawing pass-level conclusions.
- Distinguish API submission time, driver CPU time, queue wait, GPU execution, compositor latency, and display latency.
- Never optimize one captured frame without checking frame-time distributions and repeated behavior.
- Do not compare captures taken with different validation layers, debug modes, shader variants, frame limits, or presentation modes.
- Preserve raw captures and exact commands.
- Treat vendor counters as architecture-specific evidence; do not transfer thresholds blindly between GPU families.
- Measure profiler overhead. Frame capture tools can heavily perturb synchronization, memory, pipeline caching, and timing.

# Required environment record

Record this before capture:

```text
Repository/commit:
Build configuration:
Target framework/runtime:
Application executable and arguments:
Graphics framework:
Graphics API requested:
Graphics API actually selected:
Adapter name/vendor/device ID:
Integrated/discrete/software adapter:
Driver version:
OS and compositor/window system:
Resolution and render scale:
Refresh rate:
VSync/present mode:
Swapchain image count:
HDR/color format:
MSAA/sample count:
Power mode and thermal state:
Validation/debug layers enabled:
Profiler and version:
Workload sequence:
Warm-up frames/time:
Capture frame or time window:
```

For WebGPU or `wgpu-native`, also record:

```text
Backend: Metal / D3D12 / Vulkan / OpenGL / browser backend
Adapter limits and enabled features:
Surface format and alpha mode:
Timestamp-query support:
Fallback adapter status:
```

# Frame model

Split each frame into:

1. input and dispatcher latency;
2. application logic, binding, and state propagation;
3. layout, measure, arrange, and scene invalidation;
4. display-list or retained-scene generation;
5. command encoding and resource preparation;
6. native API and driver submission;
7. GPU queue wait and execution;
8. present, swapchain, or drawable handling;
9. compositor queueing and display/vsync.

A complete investigation must identify the critical path across those stages.

# Required metrics

Collect distributions, not only averages:

- end-to-end frame time p50, p90, p95, p99, maximum;
- CPU update, layout, scene, and render-thread durations;
- command encoding and submission duration;
- GPU frame and per-pass durations;
- CPU-to-GPU queue depth and frames in flight;
- present interval, display latency, and missed-frame percentage;
- hitch count above explicit thresholds;
- draw, dispatch, pass, and command-buffer counts;
- primitive, vertex, fragment, and thread-group counts where available;
- upload, copy, resolve, and readback bytes;
- GPU resource bytes, allocation count, residency/budget, and deferred-destruction backlog;
- shader occupancy, bandwidth, cache, ALU, raster, and stall counters where supported.

Frame budgets are approximately 16.67 ms at 60 Hz, 8.33 ms at 120 Hz, and 6.94 ms at 144 Hz. These are end-to-end deadlines.

# Application instrumentation

Add stable names and identifiers for:

- frame begin/end;
- update/layout/scene generation;
- command encoding;
- queue submit;
- render, compute, and copy passes;
- upload/readback batches;
- present request and completion;
- resource creation/destruction;
- shader and pipeline creation;
- cache hit/miss and atlas growth;
- swapchain recreation and resize paths.

Use API debug labels plus platform markers:

- Metal command-buffer, encoder, pass, resource, and signpost labels;
- D3D12 PIX events and object names;
- Vulkan debug-utils object names and command-buffer labels;
- OpenGL debug groups and object labels;
- WebGPU encoder/pass/resource labels;
- EventSource/EventPipe events for managed frame stages.

Prefer low-overhead production-capable telemetry behind a runtime switch.

# Portable GPU timestamp workflow

GPU timestamp queries are the first portable pass-level measurement for D3D12, Vulkan, Metal wrappers, and WebGPU implementations that expose them.

Measure:

```text
Frame
  Shadow pass
  Main opaque pass
  Transparent pass
  UI/compositor pass
  Copy/upload batch
  Post-processing pass
```

Requirements:

- query feature/support negotiated at device creation;
- query-set or query-heap capacity sized for frames in flight;
- timestamps written around meaningful passes, not every draw;
- results resolved to a readback buffer;
- results consumed asynchronously several frames later;
- device timestamp period/frequency converted correctly;
- invalid/disjoint/unavailable results rejected;
- query overhead measured with instrumentation enabled and disabled.

Never synchronously map, wait, or block for timestamp results on the measured critical path.

GPU timestamps measure queue execution intervals. They do not measure CPU command generation, driver submission, compositor latency, display scanout, or time waiting before the first timestamp executes.

# First-pass bound classification

Use CPU traces, GPU timestamps, and presentation data together:

- Long managed/update/layout time and short GPU time: application or UI CPU bound.
- Long command encoding or driver CPU time and short GPU execution: render-thread/API/driver CPU bound.
- Short CPU submission and long GPU execution: GPU execution bound.
- GPU idle gaps while CPU generates work: CPU starvation or serialization.
- CPU blocked on fences/maps while GPU has work: synchronization or resource-lifetime bottleneck.
- GPU finishes early but present is late: swapchain, compositor, vsync, drawable starvation, or frame pacing.
- High GPU utilization but stable frame time below budget: not necessarily a user-visible bottleneck.
- Both CPU and GPU exceed budget: optimize the stage on the end-to-end critical path and improve overlap.

# macOS: Metal profiling

## Tool discovery

List installed Instruments templates:

```bash
xcrun xctrace list templates
```

Locate command-line developer tools and selected Xcode:

```bash
xcode-select -p
xcrun --find xctrace
xcrun metal --version 2>/dev/null || true
system_profiler SPDisplaysDataType
```

Template names vary by Xcode version. Always query installed templates rather than assuming exact names.

## Metal System Trace with `xctrace`

When the installed template is named `Metal System Trace`:

```bash
mkdir -p artifacts/gpu

xcrun xctrace record \
  --template "Metal System Trace" \
  --time-limit 30s \
  --output artifacts/gpu/metal-system.trace \
  --launch -- ./App
```

For a framework-dependent .NET app:

```bash
xcrun xctrace record \
  --template "Metal System Trace" \
  --time-limit 30s \
  --output artifacts/gpu/metal-system.trace \
  --launch -- dotnet exec ./App.dll
```

Attach to an existing process:

```bash
PID=$(pgrep -n App)

xcrun xctrace record \
  --template "Metal System Trace" \
  --attach "$PID" \
  --time-limit 30s \
  --output artifacts/gpu/metal-system.trace
```

Open the capture:

```bash
open artifacts/gpu/metal-system.trace
```

Inspect:

- CPU submission threads and Metal driver work;
- command-buffer creation, commit, scheduling, and completion;
- encoder and pass durations;
- queue occupancy and idle gaps;
- drawable acquisition and present timing;
- resource uploads and blits;
- synchronization and command-buffer dependencies;
- GPU utilization and counters exposed by the device;
- compositor and display timing where available.

Correlate the capture with a `dotnet-trace` CPU sample for managed command generation.

## Metal GPU frame capture

Use Xcode's Metal frame capture for API-state and single-frame diagnosis. Configure capture through the executable scheme or programmatic capture APIs when needed.

Capture a representative frame after warm-up, not startup shader compilation unless startup is the target.

Inspect:

- command-buffer and encoder hierarchy;
- render-pass attachment load/store actions;
- pipeline, shader, vertex, index, texture, sampler, and buffer bindings;
- resource contents and formats;
- redundant state changes;
- unexpected intermediate textures or copies;
- draw and dispatch counts;
- shader source/correlated statistics where supported;
- per-command GPU duration and dependency chain;
- validation warnings.

Frame capture is intrusive. Validate findings with Metal System Trace and application timestamps over many frames.

## Metal counters and shader profiling

Use Xcode GPU counters or shader profiling when supported by the Mac/GPU/Xcode combination.

Look for:

- tiler versus renderer utilization;
- vertex, fragment, and compute occupancy;
- bandwidth and texture-sampling pressure;
- threadgroup memory and register pressure;
- overdraw and fragment work;
- attachment load/store bandwidth;
- tile-memory spills;
- ALU versus memory stalls;
- shader-line hotspots.

On Apple tile-based GPUs, investigate:

- unnecessary attachment stores and reloads;
- render-pass breaks that destroy tile locality;
- oversized intermediate render targets;
- blending and overdraw;
- memoryless attachment opportunities;
- storage-mode mismatches;
- CPU/GPU synchronization caused by managed/shared resources.

## Metal memory and lifetime

Combine:

- Metal System Trace;
- Instruments Allocations;
- VM Tracker;
- application resource accounting;
- heap and resource labels.

Track:

- `MTLBuffer` and `MTLTexture` allocation size;
- heap capacity and fragmentation;
- drawable count and retained drawables;
- command buffers retaining resources until completion;
- pipeline and argument-buffer caches;
- staging buffers and temporary textures;
- resize-created resources awaiting release;
- shared/managed/private storage-mode behavior.

A stable managed heap with growing resident memory can indicate native wrappers, Metal resources, deferred command-buffer retention, IOSurface/compositor surfaces, or driver-private allocations.

# Windows: PIX, WPR/WPA, GPUView, and PresentMon

## Tool discovery

Record installed versions and discover tools:

```powershell
Get-Command wpr -ErrorAction SilentlyContinue
Get-Command wpa -ErrorAction SilentlyContinue
Get-Command PresentMon -ErrorAction SilentlyContinue
Get-Command PIXWin.exe -ErrorAction SilentlyContinue
wpr -profiles
Get-CimInstance Win32_VideoController |
  Select-Object Name, DriverVersion, AdapterRAM, PNPDeviceID
```

PIX installation paths vary. Do not hard-code one path without checking the host.

## WPR/WPA GPU timeline

Start with a general system trace when the problem may include CPU scheduling, DWM, I/O, or presentation:

```powershell
New-Item -ItemType Directory -Force artifacts\gpu | Out-Null
wpr -start GeneralProfile -filemode
# Reproduce the deterministic workload.
wpr -stop artifacts\gpu\windows-general.etl
```

For graphics-specific profiles, inspect available profiles:

```powershell
wpr -profiles
```

Select the installed graphics/GPU profile appropriate to that ADK version. Profile names differ; record the exact command used.

Open the ETL in WPA and inspect:

- GPU Utilization by engine, process, context, and queue;
- CPU Usage Sampled and Precise for render/submission threads;
- DWM/compositor activity;
- DirectX events and command submissions;
- context switches, waits, ready time, and preemption;
- present history and frame intervals when providers are included;
- video-memory usage and paging when captured;
- disk/shader-cache activity during pipeline creation.

WPA is the broad system timeline. It is not a replacement for a PIX GPU capture when pipeline state or shader details are required.

## PIX Timing Capture

Use PIX Timing Capture for multi-frame CPU/GPU correlation, queue execution, synchronization, and long-running behavior.

Launch or attach through PIX, configure a bounded capture window, reproduce the workload, and save the `.wpix` capture under `artifacts/gpu/`.

Add PIX events in native or interop layers where available:

```text
Frame
Update
Layout
SceneBuild
Upload
ShadowPass
MainPass
UiPass
Present
```

Inspect:

- CPU threads and render-thread call stacks;
- D3D12 command queues and command lists;
- GPU execution lanes;
- fence signals and waits;
- queue idle bubbles;
- CPU/GPU overlap;
- frame-to-frame variability;
- copy-queue and upload behavior;
- residency/page-fault events where available;
- PIX event hierarchy.

For .NET, collect `dotnet-trace` over the same workload because PIX may not fully resolve managed JIT frames.

## PIX GPU Capture

Use a PIX GPU capture for one or a small number of representative D3D12 frames.

Inspect:

- event and draw hierarchy;
- pipeline-state objects;
- root signatures and descriptor tables;
- render-target/depth attachments;
- resource state before and after barriers;
- texture and buffer contents;
- shader input/output and debugging;
- per-event timing and counters;
- redundant barriers and transitions;
- descriptor churn;
- render-pass structure;
- overdraw and expensive draws;
- resource residency and lifetime clues.

GPU captures perturb execution. Confirm pass durations and hitch frequency with Timing Captures or application timestamps.

## GPUView

Use GPUView when the question is system-wide scheduling, queue packets, preemption, DWM interaction, or unexplained GPU bubbles.

Capture with the GPUView-provided logging scripts or the corresponding WPR graphics profile available in the installed Windows Performance Toolkit. The exact scripts and providers vary by ADK release; inspect the installed GPUView documentation and record the exact command.

GPUView is especially useful for:

- DMA packet and hardware queue timelines;
- context scheduling and preemption;
- CPU submission versus GPU execution gaps;
- DWM/compositor interaction;
- multi-process GPU contention;
- copy/render/compute engine overlap;
- present packet flow.

Do not use GPUView as the first tool for shader instruction or resource-state analysis; use PIX for those questions.

## PresentMon

Use PresentMon for repeatable frame-present and latency statistics, particularly when comparing builds.

Discover supported options first:

```powershell
PresentMon --help
```

A typical collection shape is:

```powershell
PresentMon `
  --process_name App.exe `
  --timed 30 `
  --output_file artifacts\gpu\presentmon.csv
```

Option names vary between PresentMon releases. Query `--help` and adapt rather than copying commands blindly.

Analyze:

- displayed frame interval;
- application versus displayed frame rate;
- dropped or missed presents;
- present mode;
- CPU and display latency fields exposed by the installed version;
- stutter and tail distributions.

PresentMon does not identify which render pass or shader is slow. Correlate it with PIX/WPA.

## Windows GPU memory

Use DXGI budgets/residency telemetry in the application when possible, then correlate with PIX/WPA/vendor tools.

Track:

- local and non-local video-memory budget;
- current usage and reservation;
- committed resource bytes;
- placed-resource heap bytes and fragmentation;
- upload/readback heap growth;
- descriptor-heap growth;
- transient render-target pools;
- deferred releases waiting on fences;
- swapchain buffer recreation;
- residency evictions and page faults.

# Linux: RenderDoc, Vulkan tools, `perf`, and vendor profilers

## Environment and tool discovery

Capture GPU and driver state:

```bash
mkdir -p artifacts/gpu

uname -a
lspci -nnk | grep -A3 -Ei 'vga|3d|display'
ls -l /dev/dri || true
vulkaninfo --summary 2>/dev/null || true
glxinfo -B 2>/dev/null || true
echo "XDG_SESSION_TYPE=$XDG_SESSION_TYPE"
echo "WAYLAND_DISPLAY=$WAYLAND_DISPLAY"
echo "DISPLAY=$DISPLAY"
```

Discover profilers:

```bash
command -v renderdoccmd || true
command -v qrenderdoc || true
command -v nsys || true
command -v ncu || true
command -v rgp || true
command -v intel-gpa-system-analyzer || true
command -v perf || true
```

Confirm the application is not using a software adapter such as llvmpipe, lavapipe, SwiftShader, or WARP-equivalent fallback.

## RenderDoc capture

RenderDoc is the primary cross-vendor frame debugger for Vulkan, OpenGL, and supported D3D workloads.

Launch through the RenderDoc UI for the most reliable setup, or inspect command-line support:

```bash
renderdoccmd help
renderdoccmd capture --help
```

Command-line syntax varies by RenderDoc version and target API. Record the exact invocation generated by the installed version.

Capture a warmed representative frame and inspect:

- API event hierarchy;
- command buffers, render passes, and subpasses;
- pipeline state;
- descriptor sets/bind groups and resources;
- image layouts and resource states;
- barriers and synchronization;
- texture/buffer contents;
- mesh and vertex data;
- shader debugging and disassembly;
- draw/dispatch counts;
- attachment load/store and resolve behavior;
- validation/debug messages.

RenderDoc is primarily a state and frame-debugging tool. Its timing information is not always sufficient for statistically robust performance conclusions. Validate with timestamps and vendor profilers.

## Vulkan timestamp-query workflow

Instrument command buffers with timestamp queries around passes and copies.

Requirements:

- verify `timestampComputeAndGraphics` and queue-family timestamp support;
- read `timestampPeriod` from physical-device limits;
- reset query pools safely;
- use stage masks appropriate to the measured boundaries;
- copy results asynchronously after fence completion;
- avoid `vkQueueWaitIdle` or `vkDeviceWaitIdle` in the measured loop;
- account for queue-family clock validity and wraparound.

Also collect pipeline statistics only when supported and when their overhead is acceptable.

Track validation-layer state. Vulkan validation can materially alter CPU cost and synchronization behavior.

## Linux CPU-side graphics profiling with `perf`

Record render-thread and driver CPU activity:

```bash
sudo perf record \
  -F 999 \
  -g \
  --call-graph dwarf \
  -p <PID> \
  -o artifacts/gpu/render-cpu.data \
  -- sleep 30

sudo perf report -i artifacts/gpu/render-cpu.data
```

Use `perf stat` for CPU-side command-generation efficiency:

```bash
sudo perf stat \
  -p <PID> \
  -e cycles,instructions,cache-misses,branches,branch-misses,context-switches,page-faults \
  -- sleep 30
```

Correlate native driver frames with `dotnet-trace` for managed rendering and scene generation.

High CPU in Mesa, Vulkan loader, validation, shader compiler, or proprietary driver frames indicates a CPU-side graphics bottleneck, not automatically a GPU execution bottleneck.

## NVIDIA Nsight Systems

Use Nsight Systems for multi-frame CPU/GPU timelines on supported NVIDIA systems.

Discover options:

```bash
nsys --version
nsys profile --help
```

A typical launch pattern is:

```bash
nsys profile \
  --output artifacts/gpu/nsys-report \
  --force-overwrite=true \
  ./App
```

Enable only APIs and tracing domains relevant to the installed version and workload. Excessive tracing increases overhead.

Inspect:

- CPU threads and API calls;
- Vulkan/OpenGL/CUDA queue activity where supported;
- GPU workloads and idle gaps;
- synchronization;
- memory copies;
- frame markers;
- overlap between compute, copy, and graphics.

For shader and kernel counters, use Nsight Graphics or Nsight Compute as appropriate rather than expecting Nsight Systems alone to explain occupancy or instruction stalls.

## NVIDIA Nsight Graphics

Use Nsight Graphics for frame debugging, shader profiling, range profiling, and GPU counter analysis on supported APIs and GPUs.

Inspect:

- workload ranges and per-draw/per-dispatch duration;
- SM occupancy and warp stalls;
- shader instruction and source correlation;
- memory throughput and cache behavior;
- raster, texture, and blending pressure;
- pipeline state and resources;
- synchronization and queue dependencies.

Counter names and valid interpretations vary by NVIDIA architecture. Use the tool's bottleneck guidance as evidence, not as an automatic optimization prescription.

## AMD Radeon GPU Profiler

Use Radeon GPU Profiler for Vulkan or DirectX workloads on supported AMD GPUs.

Capture using the current Radeon Developer Tool Suite workflow and record tool/driver versions. Inspect:

- command-buffer and queue timeline;
- wavefront occupancy;
- shader stages and instruction timing;
- cache and memory behavior;
- barriers and synchronization;
- render-pass structure;
- event-level GPU duration;
- pipeline state and shader statistics.

Use Radeon Memory Visualizer where available for heaps, allocations, residency, aliasing, and fragmentation.

## Intel Graphics Performance Analyzers

Use Intel GPA System Analyzer, Graphics Frame Analyzer, and Trace Analyzer on supported Intel GPUs.

Inspect:

- real-time GPU/CPU metrics;
- frame event hierarchy;
- shader and pipeline bottlenecks;
- EU occupancy and stalls;
- sampler, memory, raster, and compute utilization;
- API calls, resource state, and experiments;
- queue and system timelines.

## Linux compositor and presentation

A smooth GPU frame can still present poorly because of Wayland/X11 compositor behavior.

Record:

- compositor name/version;
- X11 versus Wayland;
- fullscreen/windowed state;
- direct-scanout eligibility;
- display scaling and mixed-refresh monitors;
- VRR state;
- PRIME/offload path;
- explicit synchronization support;
- swapchain present mode.

Investigate compositor CPU/GPU usage with system tools and vendor profilers. On hybrid-GPU systems, detect cross-device copies between render and display GPUs.

# API-specific checks

## Direct3D 12

Inspect:

- command allocator/list reset patterns;
- command-list granularity;
- graphics, compute, and copy queue overlap;
- fence waits and signal order;
- resource barriers, split barriers, and enhanced barriers where used;
- root-signature and descriptor-table churn;
- descriptor-heap rollover;
- placed-resource heap fragmentation;
- upload-ring ownership;
- pipeline-state creation and cache misses;
- residency and budget pressure;
- swapchain waitable-object and frame-latency settings.

## Vulkan

Inspect:

- command-pool and command-buffer reuse;
- render-pass/dynamic-rendering structure;
- pipeline barriers and stage/access masks;
- image layout transitions;
- descriptor-pool/set churn;
- pipeline creation and cache persistence;
- semaphore/fence ownership;
- timeline semaphore use;
- queue-family ownership transfers;
- transient attachments and memory aliasing;
- memory-type selection and host-coherency operations;
- acquire/present blocking and out-of-date recreation paths.

## Metal

Inspect:

- command-buffer count and commit cadence;
- encoder fragmentation;
- load/store actions;
- memoryless/private/shared/managed storage choices;
- heap allocation and aliasing;
- drawable acquisition timing;
- command-buffer completion handlers retaining objects;
- argument-buffer and pipeline cache behavior;
- synchronization between CPU and managed/shared resources;
- tile-memory locality and pass breaks.

## OpenGL

Inspect:

- implicit synchronization from readbacks and queries;
- buffer orphaning or persistent mapping strategy;
- state-change and binding churn;
- shader compilation/linking during frames;
- texture upload and format conversion;
- framebuffer switches;
- `glFinish`, synchronous `glReadPixels`, or blocking map calls;
- driver command-buffer flushes;
- debug versus release context behavior.

OpenGL drivers may defer work, so CPU API duration alone does not reveal GPU duration. Use timer queries and vendor profilers.

## WebGPU and `wgpu-native`

Identify adapter, backend, limits, enabled features, surface format, present mode, alpha mode, and fallback/software status.

Profile four layers separately:

1. managed scene and command generation;
2. FFI/marshalling and wrapper overhead;
3. WebGPU validation, tracking, allocation, and command translation;
4. Metal, D3D12, or Vulkan driver/GPU/presentation.

Use WebGPU timestamp queries when supported. Correlate debug labels and queue submissions with the native backend profiler.

Investigate:

- repeated pipeline/layout/bind-group creation;
- per-draw allocations or descriptor rebuilding;
- excessive `Queue.WriteBuffer` and `WriteTexture` calls;
- implicit resource initialization and clears;
- mapping and readback stalls;
- validation/tracking overhead caused by resource churn;
- surface reconfiguration and texture acquisition failures;
- backend-specific fallback paths;
- alignment padding and safety copies;
- browser GPU-process separation and IPC.

Do not assume one WebGPU pass or submission maps one-to-one to one native pass or command buffer.

For browser WebGPU, correlate:

- browser performance trace;
- main-thread and worker activity;
- browser GPU process;
- WebGPU timestamps;
- native backend capture where browser tooling permits it;
- display/compositor timing.

# Queueing and synchronization

Inspect:

- queue idle gaps and bubbles;
- CPU waits on fences or mapped buffers;
- GPU waits on semaphores, events, or fences;
- unnecessary cross-queue dependencies;
- excessive barriers and ownership transitions;
- per-frame `WaitIdle` or `DeviceWaitIdle` patterns;
- single-buffered resources that serialize frames;
- too many frames in flight causing latency;
- too few frames in flight causing starvation;
- readbacks or query resolves blocking subsequent frames;
- resource destruction queues that never drain.

Never remove synchronization without proving lifetime and ordering safety.

# Pass and command structure

Measure rather than applying universal draw-call folklore. Investigate:

- excessive tiny passes or command buffers;
- unnecessary render-target switches;
- redundant clears and attachment loads/stores;
- state, bind-group, descriptor, and pipeline churn;
- missed batching and instancing opportunities;
- oversized monolithic passes that harm overlap or tile locality;
- repeated command generation that can be cached safely;
- upload granularity and staging-copy count;
- hidden resolve, conversion, or compositor-copy passes.

# Shader and counter analysis

Use vendor counters and per-line profiling where supported. Evaluate:

- stage duration and bottleneck unit;
- wave/warp/SIMD occupancy;
- register and local-memory pressure;
- branch divergence;
- texture and cache hit rates;
- memory bandwidth and transaction efficiency;
- ALU utilization and instruction mix;
- overdraw, depth rejection, blending, and raster pressure;
- compute workgroup size and occupancy;
- vertex reuse and primitive amplification;
- synchronization and memory-dependency stalls.

A shader with fewer instructions can be slower if it increases bandwidth, register pressure, divergence, occupancy loss, or cache misses.

# Resource uploads and readbacks

Track bytes, call counts, and duration for buffer writes, texture uploads, staging copies, mapping, flush/invalidate operations, and readbacks.

Look for:

- full-resource uploads when only a range changed;
- per-object tiny uploads instead of batched/ring-buffer updates;
- transient staging allocation churn;
- synchronous map/readback;
- format conversion or swizzle copies;
- CPU-generated mipmaps or repeated texture decoding;
- immutable data recreated every frame;
- WebGPU safety copies or alignment-induced padding;
- upload buffers reused before the GPU is finished;
- readback queues that force frame serialization.

# GPU memory and lifetime

Distinguish:

- application-visible resource bytes;
- allocator block or heap bytes;
- resident versus committed/allocated bytes;
- driver-private allocations;
- staging/upload/readback pools;
- swapchain/drawable images;
- pipeline and shader caches;
- deferred destruction awaiting GPU completion;
- compositor and IOSurface/shared surfaces;
- cross-adapter shared resources.

For growth investigations capture snapshots:

1. before workload;
2. after warm-up;
3. after repeated workload;
4. after idle and queue drain;
5. after explicit cleanup;
6. after resize/device-loss recovery where relevant.

Check disposal ownership, command-buffer references, bind groups/descriptors, cached views/samplers/pipelines, pooled resources, resize paths, swapchain recreation, and device-lost recovery.

Stable managed heap does not rule out managed wrappers retaining native GPU handles.

# UI and compositor frameworks

For Avalonia, WPF, WinUI, MAUI, Skia, and custom compositors, correlate:

- invalidation;
- layout;
- retained-scene updates;
- rasterization and tessellation;
- texture, glyph, and cache uploads;
- compositor commits;
- backend command submission;
- GPU execution;
- present and display.

Look for:

- broad invalidation caused by small state changes;
- repeated tessellation, path, image, and text work;
- glyph-atlas churn and texture uploads;
- layer/render-target proliferation;
- expensive effects forcing offscreen passes;
- opacity/clip combinations that defeat batching;
- resize storms and swapchain recreation;
- UI/render-thread synchronization;
- CPU fallback rasterization;
- compositor copies caused by incompatible formats or surfaces;
- render-scale or DPI changes causing cache invalidation;
- excessive per-frame native interop calls.

# Tool-selection matrix

| Question | Primary tool | Correlate with |
|---|---|---|
| Which managed stage delays rendering? | `dotnet-trace`, EventSource markers | native timeline |
| Which GPU pass is slow? | GPU timestamps, PIX, Metal capture, vendor profiler | frame distribution |
| Why are there GPU idle bubbles? | Metal System Trace, PIX Timing, GPUView, Nsight Systems, RGP | CPU trace |
| Which resource/state is wrong or redundant? | RenderDoc, PIX GPU Capture, Metal GPU Capture | validation layers |
| Why is presentation stuttering? | PresentMon, WPA/GPUView, Metal System Trace, compositor tools | GPU timestamps |
| Why is shader execution slow? | Nsight Graphics/Compute, RGP, Intel GPA, Metal counters | source/disassembly |
| Why is GPU memory growing? | PIX/WPA, Metal tools, RMV/vendor tools, app accounting | managed/native heap |
| Is command encoding CPU-bound? | `dotnet-trace`, Instruments, WPA/PerfView, `perf` | GPU execution timeline |
| Are copies/uploads the bottleneck? | API timestamps, PIX, Metal trace, Nsight/RGP | byte counters |
| Is WebGPU overhead above backend cost? | managed trace + native backend profiler | WebGPU labels/timestamps |

# Validation protocol

Repeat the same:

- workload and input;
- resolution and render scale;
- refresh rate and display topology;
- window/fullscreen state;
- adapter and driver;
- power and thermal mode;
- presentation mode;
- swapchain image count;
- warm-up policy;
- validation/debug-layer state;
- capture settings.

Report:

```text
Metric                         Before      After       Delta
Frame time p50                 ...         ...         ...
Frame time p95                 ...         ...         ...
Frame time p99                 ...         ...         ...
Missed-frame percentage        ...         ...         ...
CPU render-thread p95          ...         ...         ...
GPU frame p95                  ...         ...         ...
Dominant pass p95              ...         ...         ...
Queue idle percentage          ...         ...         ...
Upload bytes/frame             ...         ...         ...
GPU allocated/resident bytes   ...         ...         ...
Power/energy metric            ...         ...         ...
```

Explain why the changed metric lies on the critical path. Verify correctness, image quality, resource lifetime, device-lost behavior, multiple adapters, integrated/discrete GPUs, thermal behavior, and tail frame latency.

# Common GPU profiling failures

Reject these conclusions:

- “GPU utilization is high, therefore the GPU is the bottleneck.”
- “The captured frame is fast, therefore animation is smooth.”
- “Present is late, therefore rendering is slow.”
- “The driver is hot, therefore the driver is defective.”
- “Fewer draw calls always means faster rendering.”
- “One vendor counter proves a cross-platform optimization.”
- “A frame debugger timing is equivalent to production timing.”
- “Managed memory is stable, therefore GPU resources are released.”
- “A validation-layer capture represents release performance.”
- “Average FPS proves good frame pacing.”

# Primary references

Prefer current primary documentation for the installed versions:

- Apple Metal profiling and Xcode GPU tools: https://developer.apple.com/documentation/xcode/metal-debugger
- Apple Instruments: https://developer.apple.com/documentation/xcode/instruments
- Microsoft PIX: https://devblogs.microsoft.com/pix/documentation/
- Windows Performance Toolkit: https://learn.microsoft.com/windows-hardware/test/wpt/
- GPUView: https://learn.microsoft.com/windows-hardware/drivers/display/using-gpuview
- PresentMon: https://github.com/GameTechDev/PresentMon
- RenderDoc: https://renderdoc.org/docs/
- Vulkan specification and timestamp queries: https://registry.khronos.org/vulkan/
- NVIDIA Nsight Graphics: https://developer.nvidia.com/nsight-graphics
- NVIDIA Nsight Systems: https://developer.nvidia.com/nsight-systems
- AMD Radeon GPU Profiler: https://gpuopen.com/rgp/
- AMD Radeon Memory Visualizer: https://gpuopen.com/rmv/
- Intel Graphics Performance Analyzers: https://www.intel.com/content/www/us/en/developer/tools/graphics-performance-analyzers/overview.html
- WebGPU specification: https://www.w3.org/TR/webgpu/
