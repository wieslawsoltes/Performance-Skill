# Platform-native profiling

Load every platform document relevant to the investigated system or comparison. Consult [`../command-reference.md`](../command-reference.md) for verified canonical command forms and syntax corrections.[^command-reference]

- [`macos.md`](macos.md) — Instruments, `xcrun xctrace`, scheduling, native memory, VM, filesystem/network, Metal, symbols, and export.
- [`windows.md`](windows.md) — WPR/WPA, ETW, PerfView, Visual Studio, WinDbg/SOS, native heap, I/O, PIX, GPUView, PresentMon, and symbols.
- [`linux.md`](linux.md) — `perf`, `dotnet-trace collect-linux`, eBPF/BCC, procfs, allocator tools, containers/cgroups, RenderDoc, vendor GPU tools, and compositor analysis.

A single-host investigation usually loads one document. Load several for cross-platform comparison, remote/client-server workflows, distributed services, cross-compiled artifacts, or rendering pipelines that execute on a different machine from the managed process.

Always combine native/system evidence with the relevant domain guide. Platform tools explain native, kernel, scheduler, driver, compositor, and total-process behavior; they do not replace managed runtime, retention, benchmark, or application instrumentation evidence.

## Documentation footnotes

[^command-reference]: [`../command-reference.md`](../command-reference.md).
[^xctrace]: Apple/Xcode, [`xctrace(1)`](https://keith.github.io/xcode-man-pages/xctrace.1.html).
[^wpr]: Microsoft, [Windows Performance Recorder](https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-recorder).
[^wpa]: Microsoft, [Windows Performance Analyzer](https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-analyzer).
[^perf]: Linux, [`perf-record(1)`](https://man7.org/linux/man-pages/man1/perf-record.1.html) and [`perf-sched(1)`](https://man7.org/linux/man-pages/man1/perf-sched.1.html).
[^bcc]: iovisor, [BCC](https://github.com/iovisor/bcc).
[^renderdoc]: RenderDoc, [documentation](https://renderdoc.org/docs/).