# Platform-native profiling

Load every platform document relevant to the investigated system or comparison:

- [`macos.md`](macos.md) — Instruments, `xcrun xctrace`, scheduling, native memory, VM, filesystem/network, Metal, symbols, and export.
- [`windows.md`](windows.md) — WPR/WPA, ETW, PerfView, Visual Studio, WinDbg/SOS, native heap, I/O, PIX, GPUView, PresentMon, and symbols.
- [`linux.md`](linux.md) — `perf`, `dotnet-trace collect-linux`, eBPF/BCC, procfs, allocator tools, containers/cgroups, RenderDoc, vendor GPU tools, and compositor analysis.

A single-host investigation usually loads one document. Load several for cross-platform comparison, remote/client-server workflows, distributed services, cross-compiled artifacts, or rendering pipelines that execute on a different machine from the managed process.

Always combine native/system evidence with the relevant domain guide. Platform tools explain native, kernel, scheduler, driver, compositor, and total-process behavior; they do not replace managed runtime, retention, benchmark, or application instrumentation evidence.
