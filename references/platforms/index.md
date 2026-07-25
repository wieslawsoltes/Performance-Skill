# Platform-native profiling

Load exactly one platform guide for the target host:

- [`macos.md`](macos.md) — Instruments, `xcrun xctrace`, allocations, VM, scheduling, I/O, Metal, symbols, and export.
- [`windows.md`](windows.md) — WPR/WPA, ETW, PerfView, Visual Studio, WinDbg/SOS, memory, I/O, PIX, GPUView, and PresentMon.
- [`linux.md`](linux.md) — `perf`, `dotnet-trace collect-linux`, scheduler/off-CPU analysis, eBPF, procfs, native allocators, containers, RenderDoc, and vendor GPU tools.

Correlate platform-native evidence with the relevant domain guide rather than using platform traces in isolation.
