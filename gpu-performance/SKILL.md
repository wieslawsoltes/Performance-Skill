---
name: dotnet-gpu-performance
summary: Diagnose GPU, rendering, composition, shader, synchronization, upload, residency, and presentation bottlenecks in .NET graphics applications across macOS, Windows, and Linux.
description: A GPU-focused companion to the general .NET performance skill. Covers Metal, Direct3D 11/12, Vulkan, OpenGL, WebGPU, Skia, Avalonia, WPF, WinUI, MAUI, game engines, compute workloads, platform profilers, vendor profilers, API captures, timestamps, and repeatable before/after validation.
---

# .NET GPU Performance Engineering Skill

## Mission

Use this skill when a .NET application renders through Metal, Direct3D, Vulkan, OpenGL, WebGPU, Skia, a native graphics library, or an OS compositor and the user asks to investigate frame rate, frame pacing, latency, GPU utilization, shader cost, resource uploads, GPU memory, synchronization, or presentation.

This is a companion to `../SKILL.md`. Apply the general skill for workload control, managed CPU, GC, native CPU, and total-memory evidence. Apply this skill for the graphics pipeline and GPU execution layer.

Treat every frame as a distributed pipeline. Never call an application GPU-bound merely because it uses a GPU or because GPU utilization is nonzero.

The objective is to identify which stage limits throughput or latency:

1. application and UI-thread work;
2. layout, scene construction, and invalidation;
3. render-thread command generation;
4. native graphics API and driver CPU work;
5. resource creation, mapping, copies, and uploads;
6. queue submission and synchronization;
7. GPU execution by pass, command, pipeline, and shader;
8. composition, present, display queueing, and vsync.

## Non-negotiable rules

- Profile an optimized `Release` build with the actual deployment model.
- Record GPU model, driver version, operating system, display refresh rate, resolution, scaling, HDR state, power mode, and active graphics API.
- Record whether the machine uses an integrated, discrete, external, hybrid, or software GPU.
- Confirm which adapter/device the application actually selected.
- Warm shader and pipeline caches unless cold pipeline creation is under investigation.
- Separate CPU frame time, GPU frame time, present wait, and end-to-end latency.
- Use GPU timestamps or an API profiler before assigning cost to a GPU pass.
- Do not compare captures made at different resolution, scaling, refresh rate, quality settings, or power state.
- Do not compare vendor counter values across different GPU architectures as though they had identical semantics.
- Preserve the original capture. GPU captures may replay work differently from the live application.
- Report profiler overhead, replay limitations, unavailable counters, missing shader symbols, and any forced serialization.
- Verify improvements in an uncaptured run. A frame debugger or counter collection can materially perturb execution.

# Required investigation report

Report:

1. **Symptom** — hitching, low throughput, high latency, memory growth, thermal throttling, or visual corruption.
2. **Graphics path** — framework, compositor, API, backend, adapter, swapchain, and presentation mode.
3. **Workload** — deterministic interaction, scene, resolution, frame count, and warm-up.
4. **Frame decomposition** — CPU, queue, GPU, and present timing.
5. **GPU evidence** — captures, timestamps, counters, queue timeline, shader or pass attribution.
6. **Dominant limiter** — exact stage and ownership boundary.
7. **Fix** — code, shader, resource, batching, synchronization, or presentation change.
8. **Validation** — identical before/after workload with frame-time distributions and GPU metrics.
9. **Residual risks** — architecture dependence, capture perturbation, driver variance, and remaining bottlenecks.

# Phase 1: identify the graphics stack

Before collecting data, determine:

```text
UI/framework:
Renderer/compositor:
Graphics abstraction:
Native graphics API:
Native library/backend:
GPU adapter and driver:
Swapchain format and buffer count:
Present mode / vsync:
Display refresh rate:
Render resolution and scaling:
MSAA/sample count:
HDR/color format:
Frame limiter:
Debug/validation layers enabled:
```

Typical paths include:

```text
Avalonia -> Skia -> Metal / Direct3D / Vulkan / OpenGL
Avalonia -> custom renderer -> WebGPU/wgpu-native -> Metal / D3D12 / Vulkan
WPF -> MILCore/D3D -> DWM
WinUI -> compositor / DirectComposition -> D3D
MAUI -> platform renderer -> Metal / OpenGL / D3D
C# engine -> Silk.NET/Vortice/SharpGen binding -> native API
C# WebGPU -> wgpu-native/Dawn -> Metal / D3D12 / Vulkan
Browser-hosted .NET -> WebGPU -> browser GPU process -> native API
```

The abstraction layer may hide the underlying API. Inspect runtime logs, adapter enumeration, enabled backend flags, native module loading, and device creation code rather than guessing.

# Phase 2: establish frame telemetry inside the application

External profilers answer what the system did. Application instrumentation preserves semantic ownership.

Instrument stable markers for:

- frame start and frame end;
- update and input processing;
- layout and scene build;
- render graph construction;
- command encoding;
- resource upload/copy;
- queue submit;
- present request;
- individual render, compute, and copy passes;
- pipeline and shader identifiers;
- resource creation and destruction;
- device loss and swapchain recreation.

Use names that remain stable across builds, for example:

```text
Frame
UI.Layout
Scene.Build
Render.Encode
Upload.GlyphAtlas
Upload.ImageTiles
Pass.Opaque
Pass.Text
Pass.Composite
Pass.PostProcess
Queue.Submit
Swapchain.Present
```

Do not emit per-draw managed logging in normal profiling runs. Prefer low-allocation event markers, native profiler markers, ring buffers, or aggregated counters.

## GPU timestamps

Use timestamp queries where the selected API and device support them. Measure at pass boundaries rather than synchronously timing each draw.

Required practices:

- query feature/counter support at runtime;
- allocate timestamp/query storage once and reuse it;
- resolve results asynchronously after the GPU has completed the relevant work;
- convert ticks using the device timestamp period or API-defined conversion;
- account for timestamp validity bits and wraparound where applicable;
- avoid CPU waits solely to read the current frame's timestamps;
- associate results with a frame index and queue submission;
- distinguish graphics, compute, and copy queues;
- validate whether timestamps are comparable across queues.

A CPU stopwatch around `Submit` does not measure GPU execution. It measures submission overhead and any CPU-side blocking performed by the implementation.

## Frame statistics

Collect at least:

```text
CPU update time
CPU render encoding time
native/driver submission time
GPU frame time
per-pass GPU time
present wait / acquire wait
end-to-end frame time
frames presented
frames dropped or missed
resource upload bytes/frame
draw/dispatch/copy counts
pipeline switches
render-pass count
transient and resident GPU bytes
```

Report median, p90, p95, p99, maximum, hitch count, and missed-deadline percentage. An average conceals frame-pacing failures.

# Phase 3: prove the limiting stage

Use controlled experiments together with traces.

## Resolution-scaling test

Run the same scene at 50%, 75%, 100%, and optionally 125% render resolution.

- GPU time scaling approximately with pixel count suggests fragment, bandwidth, render-target, blending, or post-processing pressure.
- Little GPU-time change suggests geometry, compute, fixed pass overhead, synchronization, presentation, or CPU limitation.
- CPU frame-time improvement from lower resolution may indicate driver command generation, readbacks, image processing, or software fallback.

Resolution scaling is evidence, not proof by itself.

## Null or reduced rendering test

Temporarily replace expensive passes with clears, minimal shaders, reduced geometry, or disabled effects while keeping frame scheduling intact.

Use this to isolate:

- scene generation versus GPU execution;
- text/image upload versus drawing;
- composition versus content rendering;
- post-processing versus base rendering;
- presentation versus offscreen work.

Do not remove so much work that queueing, resource lifetime, or compositor behavior changes beyond recognition.

## Synchronization test

Search for:

- CPU waits on fences, events, semaphores, or command-buffer completion;
- GPU queue waits and cross-queue dependencies;
- swapchain acquire/present blocking;
- implicit synchronization from mapping, readback, or resource destruction;
- per-frame device-idle calls;
- excessive frames in flight;
- insufficient frames in flight;
- reuse of transient resources before completion;
- upload-ring exhaustion.

A low-utilization GPU can still be the latency bottleneck when it is repeatedly starved or serialized.

# macOS and Metal

## Tool stack

Use:

- Instruments templates available in the installed Xcode, including Metal-related system tracing;
- Xcode Metal Debugger and GPU captures;
- Metal performance counters and per-line shader profiling where supported;
- `xcrun xctrace` for repeatable system-level recordings;
- application signposts and Metal debug groups for semantic correlation.

Discover installed templates instead of assuming names:

```bash
xcrun xctrace list templates
```

Record a Metal/system trace using the matching installed template:

```bash
xcrun xctrace record \
  --template "<installed Metal or GPU template>" \
  --time-limit 30s \
  --output artifacts/macos-gpu.trace \
  --launch -- ./App
```

For framework-dependent deployment:

```bash
xcrun xctrace record \
  --template "<installed Metal or GPU template>" \
  --time-limit 30s \
  --output artifacts/macos-gpu.trace \
  --launch -- dotnet exec ./App.dll
```

Template names and capabilities vary by Xcode and target hardware. Query first and record the exact template.

## Metal capture workflow

Use a GPU capture around a stable, representative frame or small frame range. Add debug labels to:

- command queues and command buffers;
- render/compute/blit encoders;
- textures, buffers, heaps, fences, and events;
- render and compute pipeline states.

Inspect:

- command-buffer and encoder timelines;
- pass dependencies and overlap;
- idle gaps between submissions;
- attachment load/store actions;
- tile-memory behavior on Apple GPUs;
- memoryless attachment opportunities;
- resource residency and heap usage;
- expensive render/compute passes;
- shader occupancy, limiter, bandwidth, texture, and arithmetic counters;
- redundant resolves, copies, clears, and format conversions;
- drawable acquisition and presentation timing.

Apple GPU counter collection may execute passes without their normal overlap or replay them for deterministic measurements. Treat counter-mode timings as diagnostic and validate the final change in an ordinary run.

## Metal-specific failure patterns

- Calling `waitUntilCompleted` in the frame loop.
- Acquiring the next drawable too early and reducing compositor flexibility.
- Holding drawables longer than necessary.
- Excessive command buffers or encoders for tiny workloads.
- Incorrect load/store actions that force unnecessary memory traffic.
- Frequent texture/buffer allocation instead of reuse or heaps.
- Managed wrappers retaining Metal resources after logical disposal.
- Uploads through poorly chosen storage modes.
- Readbacks or synchronization through shared resources.
- Pipeline compilation during interactive frames.
- Treating unified memory as cost-free; bandwidth, residency, cache behavior, and synchronization still matter.

# Windows: Direct3D, DXGI, DWM, and ETW

## System timeline first

Use WPR/WPA to correlate:

- application UI and render threads;
- D3D runtime and driver CPU work;
- GPU engine utilization;
- hardware queues and packet execution;
- DXGI presents;
- DWM composition;
- display/vsync events;
- process working set and video-memory pressure.

Query installed profiles:

```powershell
wpr -profiles
```

Record a graphics-capable profile available on the host, reproduce the workload, and stop to ETL:

```powershell
wpr -start <installed graphics profile> -filemode
# reproduce
wpr -stop artifacts\windows-gpu.etl
```

Open in WPA. Correlate CPU Usage, GPU Usage, Video Memory, DWM, DXGI/Present, and frame-analysis tables available in the installed toolkit.

## PIX

Use PIX for Direct3D 12 GPU captures and timing captures. PIX GPU profiling is applicable to D3D12 workloads and D3D11 workloads routed through D3D11-on-12; verify the actual path before relying on it.

Use:

- Timing Capture for CPU/GPU timelines, queue synchronization, residency, and frame pacing;
- GPU Capture for API events, resources, pipeline state, shader analysis, and pass cost;
- PIX events and markers for semantic regions;
- D3D12 debug layer and GPU-based validation for correctness before performance analysis.

Inspect:

- execution duration per event and queue;
- barriers and state transitions;
- fence waits and queue bubbles;
- descriptor heap behavior;
- pipeline-state creation and switches;
- resource uploads and copies;
- residency and budget pressure;
- render-target and depth operations;
- root signature and binding overhead;
- shader occupancy, wave behavior, cache and memory pressure when counters are supported.

A GPU capture is a replay-oriented artifact. Use it to locate expensive commands and state, then validate with a timing capture and uncaptured application telemetry.

## GPUView and PresentMon

Use GPUView when the problem is system-wide scheduling, queue packets, context execution, DWM, or unexplained bubbles that higher-level tools do not expose clearly.

Use PresentMon-compatible tooling for presentation statistics and frame pacing where appropriate. Distinguish:

- application render completion;
- present submission;
- compositor processing;
- displayed frame;
- dropped or repeated frame;
- independent flip, composed flip, or blit presentation paths.

Do not equate present-call duration with display latency.

## Direct3D-specific failure patterns

- `Flush`, fence waits, or readbacks in the frame loop.
- Per-frame committed resource creation instead of suballocation/reuse.
- Descriptor heap exhaustion or excessive descriptor copying.
- Overly conservative resource barriers.
- Upload heap misuse and redundant CPU-to-GPU copies.
- Pipeline-state creation during active rendering.
- Excessive command-list fragmentation.
- Swapchain configuration that forces an inferior presentation path.
- DWM/compositor limitation incorrectly attributed to shader cost.
- Video-memory budget pressure causing paging or eviction.

# Linux: Vulkan, OpenGL, compositor, and driver tooling

## System and CPU/driver context

Use the general skill's `perf`, scheduler, eBPF, and memory workflow to determine whether the render thread or graphics driver consumes CPU or blocks.

Record:

```bash
sudo perf record \
  -F 999 \
  -g \
  --call-graph dwarf \
  -p <PID> \
  -o artifacts/linux-render-cpu.data \
  -- sleep 30
```

Inspect loaded Vulkan/OpenGL drivers, selected device, Wayland/X11 path, compositor, PRIME/offload configuration, and container device access.

## Vulkan tooling

Use, as supported by the target GPU and driver:

- RenderDoc for frame capture and API/resource inspection;
- Vulkan timestamp queries and pipeline statistics;
- validation layers for correctness, disabled for final performance measurements;
- NVIDIA Nsight Graphics on supported NVIDIA hardware;
- AMD Radeon GPU Profiler on supported AMD hardware;
- Intel Graphics Performance Analyzers or platform tools on supported Intel hardware;
- vendor driver performance overlays and counters.

Inspect:

- queue submissions and semaphore/fence dependencies;
- pipeline barriers and stage/access masks;
- image layouts and transitions;
- render-pass or dynamic-rendering boundaries;
- attachment load/store operations;
- descriptor updates and pipeline switches;
- transient allocations and staging copies;
- transfer/graphics/compute queue overlap;
- pipeline cache misses and runtime compilation;
- sparse/residency behavior;
- swapchain acquire/present and compositor interaction.

Validation layers can radically change CPU cost and synchronization. Fix validation errors first, then disable validation for representative performance collection.

## OpenGL tooling

Use vendor profilers, RenderDoc where supported, API debug output for correctness, and GPU timer queries for pass-level timing.

Search for:

- implicit synchronization from `glFinish`, readbacks, buffer mapping, or query retrieval;
- driver shader compilation during frames;
- excessive state changes and tiny draws;
- buffer orphaning or synchronization mistakes;
- texture upload and format conversion;
- compositor and swap interval behavior.

OpenGL driver work may appear asynchronously on helper threads. Correlate process-wide CPU stacks with GPU timers and frame captures.

## Linux-specific failure patterns

- Running on llvmpipe/software rendering unexpectedly.
- Selecting an integrated GPU when the workload expects a discrete GPU.
- PRIME render offload or environment variables selecting the wrong adapter.
- Container missing `/dev/dri`, required groups, or GPU runtime integration.
- Wayland/X11 compositor or presentation mode limiting frame pacing.
- Validation layers, overlays, capture layers, or debug drivers left enabled.
- Shader or pipeline cache not persisted between runs.
- CPU governor, thermal state, or GPU power state changing between captures.

# Vendor profilers

## NVIDIA Nsight Graphics

Use Nsight Graphics for supported Direct3D, Vulkan, OpenGL, and OpenXR workloads on supported NVIDIA GPUs.

Choose the activity that matches the question:

- Graphics/Frame Capture for API state, resources, dependencies, and rendering correctness;
- GPU Trace for GPU unit utilization, queue execution, bubbles, throughput, and async-compute opportunities;
- Shader Profiler for source/disassembly hot spots and stall reasons;
- memory views for heaps, budgets, and resource usage where supported.

Record tool, driver, GPU architecture, clock-lock behavior, capture settings, and whether other GPU workloads were active.

## AMD Radeon GPU Profiler

Use Radeon GPU Profiler for supported Vulkan and DirectX 12 applications on compatible AMD hardware. Inspect:

- command-buffer and queue timelines;
- wavefront occupancy;
- shader and event timing;
- cache and memory behavior;
- barriers, stalls, and dependencies;
- asynchronous compute overlap;
- GPU memory and resource behavior with companion Radeon tools.

Use Radeon Developer Panel or the currently documented capture mechanism for the installed version. Do not assume capture commands across versions.

## Intel graphics tools

Use Intel Graphics Performance Analyzers or current Intel platform tooling on supported devices. Inspect frame streams, GPU metrics, shaders, draw calls, overdraw, bandwidth, and media/compute engines as supported.

## Cross-vendor captures

RenderDoc is excellent for frame inspection and coarse event timing but is not a universal substitute for hardware-counter profilers. Use the vendor profiler when the question concerns microarchitectural occupancy, cache behavior, wave/warp stalls, or specific execution units.

# WebGPU and wgpu-native

WebGPU adds an abstraction layer but does not remove native GPU behavior.

For native .NET applications using wgpu-native, Dawn, or another implementation:

1. identify the selected backend and adapter;
2. collect managed and native CPU traces around command encoding and FFI;
3. use WebGPU timestamp queries when the feature is supported;
4. label passes and resources through the implementation's available debug-label APIs;
5. capture the underlying Metal, D3D12, or Vulkan workload with platform/vendor tools when compatible;
6. correlate WebGPU submissions with native queue activity;
7. inspect implementation logs for implicit copies, fallback paths, validation, and device limits.

For browser-hosted .NET/WebAssembly:

- browser developer tools can expose frame, main-thread, compositor, and limited GPU-process evidence;
- WebGPU timestamp-query availability is feature- and browser-dependent;
- native platform profilers may attribute work to the browser GPU process rather than the .NET/WASM process;
- cross-process correlation requires explicit application markers, browser tracing, and stable frame identifiers;
- browser security and privacy constraints may restrict counters and timestamp precision.

Do not assume a WebGPU pass maps one-to-one to a native render pass after backend translation and optimization.

# UI frameworks and compositors

## Avalonia and Skia

Separate:

- UI-thread layout/binding cost;
- render-scene generation;
- compositor invalidation and batching;
- Skia display-list/command generation;
- glyph, image, and path cache behavior;
- texture upload and atlas churn;
- native backend execution;
- OS compositor and presentation.

A hot Skia CPU raster path may indicate software fallback, readback, unsupported effect, or intentional CPU rendering rather than a GPU shader bottleneck.

## WPF

Correlate ETW/WPA, DWM, and application evidence. Determine whether rendering is hardware accelerated, tier-limited, software-rendered, or constrained by dirty-region, layout, bitmap effect, interop, or composition behavior.

## WinUI and DirectComposition

Distinguish application rendering from compositor animations and DWM presentation. A smooth compositor animation can coexist with a blocked UI thread; conversely, low application CPU does not prove the compositor or GPU meets the display deadline.

# GPU memory and resource lifetime

Track both logical and physical concepts:

- resource size requested by the application;
- allocator block and heap size;
- committed versus suballocated memory;
- resident versus evicted resources;
- transient aliasing;
- staging/upload/readback memory;
- driver-private allocations;
- duplicated resources across adapters or processes;
- swapchain, compositor, and capture overhead;
- managed wrapper lifetime versus native resource lifetime.

Use stable resource IDs, labels, creation stacks where practical, and deferred-destruction queue telemetry.

For explicit APIs, destruction by the managed wrapper does not imply immediate physical reclamation. Resources may remain alive until all referencing GPU submissions complete.

Investigate growth with a sequence:

1. capture managed heap and wrapper counts;
2. capture process RSS/private memory;
3. capture API/vendor GPU memory and residency;
4. stop workload and wait for GPU idle only as a diagnostic experiment;
5. drain deferred release queues;
6. compare logical resource registry against profiler memory;
7. identify unbounded caches, never-signaled fences, retained command buffers, or forgotten views.

Do not insert `DeviceWaitIdle` or an equivalent into production merely to make memory graphs fall sooner.

# Shader analysis

For an expensive shader or pipeline, inspect:

- invocation count and dispatch/draw dimensions;
- active lanes/threads and divergence;
- occupancy and register pressure;
- arithmetic versus memory limitation;
- texture sampling and cache behavior;
- bandwidth and render-target traffic;
- overdraw and rejected fragments;
- subgroup/wave operations;
- synchronization and shared/threadgroup memory;
- precision and data width;
- compiler-generated ISA/disassembly;
- specialization constants and permutation count.

Optimize the highest aggregate cost, not merely the slowest single invocation.

Validate shader changes for image correctness, precision, determinism, architecture portability, and pipeline-cache effects.

# Common optimization classes

Apply only when supported by evidence:

- reduce redundant invalidation and scene rebuilds;
- batch compatible draws or dispatches;
- reduce state and pipeline switches;
- merge or split passes based on measured attachment and synchronization cost;
- remove unnecessary barriers and waits without violating hazards;
- overlap independent compute, graphics, and transfers;
- use persistent upload rings and staging pools;
- avoid per-frame resource and pipeline creation;
- cache pipelines and shader variants;
- reduce overdraw and intermediate render targets;
- select appropriate formats, sample counts, and resolutions;
- use transient/aliasable/memoryless resources where semantically valid;
- improve resource residency and budget handling;
- reduce readbacks and CPU/GPU round trips;
- shorten drawable/swapchain image ownership;
- tune frame-in-flight count;
- move work to compositor animations where the platform supports it and semantics allow it.

# Validation matrix

A complete GPU optimization report should include:

```text
Metric                           Before       After        Delta
CPU frame p50                    ...          ...          ...
CPU frame p95                    ...          ...          ...
CPU render/encode p95            ...          ...          ...
GPU frame p50                    ...          ...          ...
GPU frame p95                    ...          ...          ...
Present-to-display p95           ...          ...          ...
Missed display deadlines         ...          ...          ...
Hitches above threshold          ...          ...          ...
Dominant pass GPU time           ...          ...          ...
Draw/dispatch/copy count         ...          ...          ...
Upload bytes/frame               ...          ...          ...
Resident GPU memory              ...          ...          ...
Peak GPU memory                  ...          ...          ...
Power/clock/thermal state        ...          ...          ...
```

Validate across:

- at least one uncaptured run;
- cold and warm caches when relevant;
- representative integrated and discrete GPUs when supported;
- target refresh rates and resolutions;
- windowed/fullscreen and compositor paths when relevant;
- idle, steady-state, burst, resize, animation, and content-change scenarios.

# Agent operating procedure

When acting as a coding agent:

1. Read `../SKILL.md` and establish the controlled workload.
2. Identify the concrete graphics path and adapter.
3. Add stable application markers and per-pass GPU timestamps if absent and feasible.
4. Capture a platform system timeline to classify CPU, GPU, synchronization, or presentation limitation.
5. Capture a representative frame or GPU trace with the API/vendor profiler.
6. Attribute cost to a pass, queue dependency, shader, upload, resource, or present path.
7. Change the smallest high-leverage component.
8. Keep correctness/validation layers available, but disable their overhead for final performance runs.
9. Re-run identical workloads and compare distributions, not screenshots or subjective smoothness.
10. Preserve capture commands and metadata beside artifacts.
11. Keep large traces out of Git unless repository policy explicitly requires them.
12. Report any tool or hardware limitation that prevents a definitive attribution.

# Common false conclusions

Reject:

- “GPU utilization is 100%, therefore shaders are the problem.”
- “GPU utilization is low, therefore the GPU is not limiting latency.”
- “Submit took 0.2 ms, therefore the GPU frame took 0.2 ms.”
- “The average is 60 FPS, therefore pacing is smooth.”
- “A frame capture replay is identical to live execution.”
- “Unified memory means GPU memory cannot leak.”
- “Disposing the managed wrapper immediately frees physical GPU memory.”
- “More frames in flight always improves performance.”
- “One barrier is cheap, therefore thousands are cheap.”
- “A vendor metric has the same meaning on every architecture.”
- “RenderDoc event timing replaces hardware-counter profiling.”
- “Validation-layer performance is representative.”
- “WebGPU prevents backend-specific bottlenecks.”

# References

Prefer primary documentation and verify the installed tool version:

- Apple Metal debugger: https://developer.apple.com/documentation/xcode/metal-debugger
- Apple GPU counter analysis: https://developer.apple.com/documentation/xcode/analyzing-apple-gpu-performance-using-counter-statistics
- Apple Metal GPU counters: https://developer.apple.com/documentation/metal/gpu-counters-and-counter-sample-buffers
- Microsoft PIX overview: https://learn.microsoft.com/windows/win32/direct3dtools/pix/articles/general/pix-overview
- Microsoft PIX GPU captures: https://learn.microsoft.com/windows/win32/direct3dtools/pix/articles/gpu-captures/pix-gpu-captures
- Windows Performance Toolkit: https://learn.microsoft.com/windows-hardware/test/wpt/
- NVIDIA Nsight Graphics: https://developer.nvidia.com/nsight-graphics
- AMD Radeon GPU Profiler: https://gpuopen.com/rgp/
- Intel Graphics Performance Analyzers: https://www.intel.com/content/www/us/en/developer/tools/graphics-performance-analyzers/overview.html
- RenderDoc: https://renderdoc.org/
- Vulkan specification and query/timestamp documentation: https://registry.khronos.org/vulkan/
- WebGPU specification: https://www.w3.org/TR/webgpu/
