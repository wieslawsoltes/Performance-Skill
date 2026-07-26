# GPU and rendering

Use [`guide.md`](guide.md) for the complete operational GPU and rendering profiling playbook. Consult [`../command-reference.md`](../command-reference.md) before running native or vendor profiler commands.[^command-reference]

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

## Documentation footnotes

[^command-reference]: [`../command-reference.md`](../command-reference.md).
[^metal]: Apple, [Metal debugger and profiling](https://developer.apple.com/documentation/xcode/metal-debugger).
[^pix]: Microsoft, [PIX on Windows](https://devblogs.microsoft.com/pix/).
[^presentmon]: GameTechDev, [PresentMon console application](https://github.com/GameTechDev/PresentMon/blob/main/README-ConsoleApplication.md).
[^gpuview]: Microsoft, [GPUView](https://learn.microsoft.com/windows-hardware/drivers/display/using-gpuview).
[^renderdoc]: RenderDoc, [documentation](https://renderdoc.org/docs/).
[^nsight]: NVIDIA, [developer tools overview](https://developer.nvidia.com/tools-overview).
[^rgp]: AMD, [Radeon GPU Profiler](https://gpuopen.com/rgp/).
[^rmv]: AMD, [Radeon Memory Visualizer](https://gpuopen.com/rmv/).
[^intel-gpa]: Intel, [Graphics Performance Analyzers](https://www.intel.com/content/www/us/en/developer/tools/graphics-performance-analyzers/overview.html).
[^webgpu]: W3C, [WebGPU specification](https://www.w3.org/TR/webgpu/).