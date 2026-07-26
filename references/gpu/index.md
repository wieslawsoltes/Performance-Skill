# GPU and rendering

Use [`guide.md`](guide.md) for the complete operational GPU and rendering profiling playbook.

## Topic map

- Environment, frame model, instrumentation, timestamps, and bound classification: opening sections.
- macOS Metal and Instruments workflows: macOS section.
- Windows WPR/WPA, PIX, GPUView, PresentMon, and Direct3D workflows: Windows section.
- Linux RenderDoc, Vulkan/OpenGL, compositor, and NVIDIA/AMD/Intel tools: Linux section.
- Queueing, synchronization, pass structure, shaders, uploads/readbacks, memory, WebGPU/wgpu-native, UI compositors, and validation: cross-platform sections.

## Review guardrails

- Verify the graphics API and adapter actually selected; detect software fallback before interpreting GPU metrics.
- Use a long-enough timeline for frame pacing and one representative frame capture for API/resource state. Neither replaces the other.
- GPU timestamps measure queue execution, not CPU command generation, driver submission, compositor latency, or display scanout.
- Keep validation/debug-layer state, resolution, refresh rate, present mode, adapter, power mode, and frames in flight identical between comparisons.
- Vendor counters are architecture-specific; do not transfer thresholds between GPU families.
- Correlate managed scene/command generation with native API, driver, queue, compositor, and presentation evidence.

Always pair this guide with every relevant platform document through [`../platforms/index.md`](../platforms/index.md) and with managed/runtime evidence when .NET command generation is involved.
