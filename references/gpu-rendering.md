# GPU and rendering performance

Use this reference together with the target platform document. The goal is to prove which stage owns latency, throughput loss, memory growth, or frame instability.

## Frame model

Split each frame into:

1. input and dispatcher latency;
2. application logic, binding, and state propagation;
3. layout, measure, arrange, and scene invalidation;
4. display-list/scene generation;
5. command encoding and resource preparation;
6. native API and driver submission;
7. GPU queue wait and execution;
8. present/swapchain/drawable handling;
9. compositor queueing and display/vsync.

Do not use “GPU-bound” as shorthand for slow graphics. Prove the critical path.

## Required metrics

Collect distributions, not only averages:

- end-to-end frame time p50/p90/p95/p99/max;
- CPU frame and render-thread duration;
- command encoding/submission duration;
- GPU frame and per-pass durations;
- CPU-to-GPU queue depth;
- present interval, display latency, and missed-frame percentage;
- hitch count above explicit thresholds;
- draw/dispatch count, primitive count, upload/readback bytes;
- GPU resource bytes, residency/budget, allocation count, and lifetime backlog.

Frame budgets are approximately 16.67 ms at 60 Hz, 8.33 ms at 120 Hz, and 6.94 ms at 144 Hz. These are end-to-end deadlines.

## Instrumentation

Add stable names and identifiers for:

- frame begin/end;
- update/layout/scene generation;
- command encoding;
- queue submit;
- render, compute, and copy passes;
- upload/readback batches;
- present request and completion;
- resource creation/destruction;
- shader and pipeline creation.

Use platform signposts/markers plus API debug labels. Prefer low-overhead production-capable telemetry behind a runtime switch.

### GPU timestamps

Use timestamp queries around meaningful passes and copy operations. Resolve asynchronously after sufficient frames in flight. Never synchronously map or wait for query results on the measured critical path.

Account for:

- timestamp period/frequency conversion;
- device support and feature negotiation;
- unavailable/disjoint timestamps;
- query resolve/copy overhead;
- delayed readback;
- multi-queue clocks and comparability;
- instrumentation perturbation.

GPU timestamps measure queue execution intervals, not CPU submission, compositor latency, or display scanout.

## Bound classification

- Long managed/update/layout time, short render/GPU time: application or UI CPU bound.
- Long command encoding/driver time, short GPU execution: render-thread, API, or driver CPU bound.
- Short CPU submission, long GPU execution: GPU bound.
- CPU and GPU overlap poorly with idle GPU gaps: CPU starvation or excessive serialization.
- GPU work completes early but presents are late: swapchain, compositor, vsync, frame pacing, or drawable starvation.
- Both CPU and GPU are long: optimize the actual critical path first; parallel overlap may be as valuable as reducing either duration.

## Queueing and synchronization

Inspect:

- queue idle gaps and bubbles;
- CPU waits on fences or mapped buffers;
- GPU waits on semaphores/events/fences;
- unnecessary cross-queue dependencies;
- excessive barriers and ownership transitions;
- per-frame `WaitIdle`/`DeviceWaitIdle` patterns;
- single-buffered resources that serialize frames;
- too many frames in flight causing latency;
- too few frames in flight causing starvation;
- readbacks or query resolves blocking subsequent frames.

Never remove synchronization without proving lifetime and ordering safety.

## Pass and command structure

Measure rather than applying universal draw-call folklore. Investigate:

- excessive tiny passes or command buffers;
- unnecessary render-target switches;
- redundant clears and attachment loads/stores;
- state churn, bind-group/descriptor churn, and pipeline switches;
- missed batching/instancing opportunities;
- oversized monolithic passes that harm overlap or tile locality;
- repeated command generation that can be cached safely;
- upload granularity and staging-copy count.

## Shader analysis

Use GPU/vendor counters and per-line profiling where supported. Evaluate:

- stage duration and bottleneck unit;
- wave/warp occupancy;
- register and local-memory pressure;
- branch divergence;
- texture/cache hit rates;
- memory bandwidth and transaction efficiency;
- ALU utilization and instruction mix;
- overdraw, depth rejection, blending, and raster pressure;
- compute workgroup size and occupancy;
- vertex reuse and primitive amplification.

A shader with fewer instructions can be slower if it increases bandwidth, register pressure, divergence, or cache misses.

## Resource uploads and readbacks

Track bytes and frequency for buffer writes, texture uploads, staging copies, mapping, flush/invalidate operations, and readbacks.

Look for:

- full-resource uploads when only a range changed;
- per-object tiny uploads instead of batched/ring-buffer updates;
- transient staging allocation churn;
- synchronous map/readback;
- format conversion or swizzle copies;
- CPU-generated mipmaps or repeated texture decoding;
- immutable data recreated every frame;
- WebGPU safety copies or alignment-induced padding.

Use persistently managed upload/ring strategies only with correct per-frame ownership and fencing.

## GPU memory and lifetime

Distinguish:

- application-visible resource bytes;
- allocator block/heap bytes;
- resident versus committed/allocated bytes;
- driver-private allocations;
- staging/upload/readback pools;
- swapchain/drawable images;
- pipeline/shader caches;
- deferred destruction awaiting GPU completion;
- compositor surfaces.

For growth investigations capture snapshots before workload, after warm-up, after repeated workload, after idle/drain, and after explicit cleanup. Stable managed heap does not rule out wrapper retention or native/GPU leaks.

Check disposal ownership, command-buffer references, bind groups/descriptors, cached views/samplers/pipelines, pooled resources, resize/recreation paths, and device-lost recovery.

## WebGPU and wgpu-native

Identify adapter, backend, device, limits, enabled features, surface format, present mode, alpha mode, and fallback/software status.

Profile four distinct layers:

1. managed command and scene generation;
2. FFI/marshalling and native wrapper overhead;
3. WebGPU implementation validation, tracking, allocation, and command translation;
4. backend API, driver, GPU, and presentation.

Correlate WebGPU debug labels and timestamp queries with Metal, D3D12, or Vulkan native captures. Do not assume one WebGPU pass or submission maps one-to-one to a backend pass or command buffer.

Investigate:

- repeated pipeline/layout/bind-group creation;
- per-draw allocations or descriptor rebuilding;
- excessive `Queue.WriteBuffer`/`WriteTexture` calls;
- implicit initialization and clears;
- mapping and readback stalls;
- validation/tracking overhead from pathological resource churn;
- surface reconfiguration and texture acquisition failures;
- backend-specific fallback paths;
- browser GPU-process separation and IPC when running WebGPU in a browser.

For browser workloads correlate main thread, worker, browser GPU process, WebGPU timestamps, and browser tracing. Process CPU attributed to the app alone may omit substantial GPU-process work.

## UI and compositor frameworks

For Avalonia, WPF, WinUI, MAUI, Skia, and custom compositors, correlate invalidation, layout, retained-scene updates, rasterization, texture/cache uploads, compositor commits, backend command submission, GPU execution, and present.

Look for:

- broad invalidation caused by small state changes;
- repeated tessellation/path/text work;
- glyph atlas churn and texture uploads;
- layer/render-target proliferation;
- expensive effects forcing offscreen passes;
- opacity/clip combinations that defeat batching;
- resize storms and swapchain recreation;
- UI/render thread synchronization;
- CPU fallback rasterization;
- compositor copies caused by incompatible formats or surfaces.

## Validation

Repeat the same workload, resolution, refresh rate, window state, adapter, power mode, presentation mode, warm-up, and capture settings.

Report before/after values and explain why the changed metric lies on the critical path. Verify correctness, image quality, resource lifetime, device-lost behavior, multiple adapters, integrated/discrete GPUs, thermal/power behavior, and tail frame latency.
