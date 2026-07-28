# Verified command reference

This file is the authoritative command-syntax layer for the skill. When a longer guide conflicts with this file, use this file, inspect the installed tool's help, and update the guide.

## .NET diagnostics

```bash
dotnet-counters ps
dotnet-counters monitor --process-id <PID> --counters System.Runtime
dotnet-counters collect \
  --process-id <PID> \
  --refresh-interval 1 \
  --format csv \
  --output artifacts/performance/counters.csv \
  --counters System.Runtime
```

On Linux and macOS, PID/name attachment requires the tool and target to share `TMPDIR`.[^dotnet-counters]

```bash
dotnet-trace collect \
  --process-id <PID> \
  --profile dotnet-common,dotnet-sampled-thread-time \
  --duration 00:00:30 \
  --output artifacts/performance/runtime.nettrace
```

When no profile/provider options are supplied, current `dotnet-trace collect` defaults to `dotnet-common,dotnet-sampled-thread-time`. The historical standard `cpu-sampling` profile was removed. `cpu-sampling` remains a valid perf-based profile for `dotnet-trace collect-linux`.[^dotnet-trace]

```bash
dotnet-trace collect \
  --profile dotnet-common,dotnet-sampled-thread-time \
  --output artifacts/performance/startup.nettrace \
  --show-child-io \
  -- dotnet exec ./App.dll
```

```bash
dotnet-gcdump collect --process-id <PID> --output artifacts/performance/heap.gcdump
dotnet-gcdump report artifacts/performance/heap.gcdump
```

A GC dump triggers a generation 2 collection and can suspend a large process.[^dotnet-gcdump]

```bash
dotnet-dump collect --process-id <PID> --type Full --output artifacts/performance/process.dmp
dotnet-dump analyze artifacts/performance/process.dmp
```

`dotnet-dump` provides managed/SOS analysis and is not a native debugger.[^dotnet-dump]

## BenchmarkDotNet

Use a pinned package version in committed projects. Current runtime constants use names such as `CoreRuntime.Core10_0`, not `Core100`.[^benchmarkdotnet-runtime]

```bash
dotnet run -c Release --project Project.Benchmarks -- --list flat
dotnet run -c Release --project Project.Benchmarks -- --filter '*HotPath*'
```

BenchmarkDotNet command-line options and APIs depend on the pinned release; use the generated `--help` output and official documentation for that version.[^benchmarkdotnet]

## macOS Instruments and `xctrace`

Discover capabilities first:

```bash
xcodebuild -version
xcrun xctrace help
xcrun xctrace help record
xcrun xctrace help export
xcrun xctrace list templates
xcrun xctrace list devices
```

Canonical recording forms:

```bash
xcrun xctrace record \
  --template 'Time Profiler' \
  --time-limit 30s \
  --output artifacts/performance/macos/cpu.trace \
  --launch -- ./App
```

Framework-dependent launch:

```bash
dotnet_host="$(command -v dotnet)"
test -x "$dotnet_host"
xcrun xctrace record \
  --template 'Time Profiler' \
  --time-limit 30s \
  --output artifacts/performance/macos/dotnet-cpu.trace \
  --launch -- "$dotnet_host" exec ./App.dll
```

`xctrace` launch targets are not guaranteed to be resolved through the invoking
shell's `PATH`. Resolve command-line hosts such as `dotnet` first and pass the
absolute executable path. A failed launch can still leave a trace bundle, so verify
run issues, target output, and the expected workload result before accepting it.

```bash
xcrun xctrace record \
  --template 'Time Profiler' \
  --attach <PID> \
  --time-limit 30s \
  --output artifacts/performance/macos/cpu.trace
```

`xctrace export` changed input syntax across Xcode releases. If
`xcrun xctrace help export` lists `--input <file>`, use:

```bash
xcrun xctrace export \
  --input artifacts/performance/macos/cpu.trace \
  --toc \
  --output artifacts/performance/macos/cpu-toc.xml
```

If the installed help instead documents a positional trace, place the trace path
immediately after `export`. Prefer `scripts/xctrace-export.py` when this skill is
available locally; it detects the installed form before executing. Template and
instrument names vary by installation, and output paths generally must not already
exist.[^xctrace]

## Windows Performance Toolkit and graphics tools

```powershell
wpr -profiles
wpr -start GeneralProfile -filemode
# reproduce the bounded workload
wpr -stop artifacts\performance\windows\general.etl
wpa artifacts\performance\windows\general.etl
```

WPR profile availability and names depend on the installed Windows Performance Toolkit.[^wpr][^wpa]

```powershell
PresentMon.exe `
  --process_id <PID> `
  --timed 30 `
  --terminate_after_timed `
  --output_file artifacts\performance\windows\presentmon.csv
```

PresentMon CLI options evolve; verify them with `PresentMon.exe --help`. The current console application documents `--process_id`, `--timed`, `--terminate_after_timed`, and `--output_file`.[^presentmon]

PerfView, PIX, GPUView, and WinDbg workflows are partly interactive. Use each installed version's help and official documentation rather than inventing unsupported automation switches.[^perfview][^pix][^gpuview][^windbg]

## Linux `perf`, eBPF, and native allocation tools

CPU sampling:

```bash
sudo perf record \
  -F 999 \
  -g \
  --call-graph dwarf \
  -p <PID> \
  -o artifacts/performance/linux/cpu.data \
  -- sleep 30
sudo perf report -i artifacts/performance/linux/cpu.data
```

Scheduler recording is command-oriented. Do not use `perf sched record -p <PID>` as a portable documented form:

```bash
sudo perf sched record -- sleep 30
sudo perf sched timehist -p <PID>
sudo perf sched latency -p
```

`-p` means different things for `timehist`, `map`, and `latency`; inspect `perf sched <subcommand> --help` on the host.[^perf-record][^perf-sched]

```bash
sudo perf stat \
  -p <PID> \
  -e cycles,instructions,cache-references,cache-misses,branches,branch-misses,context-switches,cpu-migrations,page-faults \
  -- sleep 30
```

BCC tool filenames differ by distribution (`runqlat`, `runqlat-bpfcc`, and similar). Always run `<tool> --help`; duration flags are tool-specific. Do not assume a positional duration is accepted.[^bcc]

```bash
heaptrack ./App
heaptrack --pid <PID>
```

Attach support and syntax depend on the installed heaptrack version.[^heaptrack]

```bash
valgrind --tool=massif --massif-out-file=artifacts/performance/linux/massif.out ./App
ms_print artifacts/performance/linux/massif.out
valgrind --tool=memcheck --leak-check=full ./App
```

Valgrind substantially perturbs managed/native applications and should be used only for focused investigations.[^valgrind]

## GPU/API tools

RenderDoc, NVIDIA Nsight, AMD Radeon GPU Profiler/Memory Visualizer, Intel GPA, PIX, and Xcode Metal capture have version-, API-, driver-, and target-specific launch workflows. Prefer their UI/launcher or documented CLI for the installed release and preserve the capture version with the artifact.[^renderdoc][^nsight][^rgp][^rmv][^intel-gpa][^metal-tools]

## Documentation footnotes

[^dotnet-counters]: Microsoft, [`dotnet-counters` diagnostic tool](https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-counters).
[^dotnet-trace]: Microsoft, [`dotnet-trace` diagnostic tool](https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-trace).
[^dotnet-gcdump]: Microsoft, [`dotnet-gcdump` diagnostic tool](https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-gcdump).
[^dotnet-dump]: Microsoft, [`dotnet-dump` diagnostic tool](https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-dump).
[^benchmarkdotnet]: BenchmarkDotNet, [official documentation](https://benchmarkdotnet.org/).
[^benchmarkdotnet-runtime]: BenchmarkDotNet, [`CoreRuntime` API](https://benchmarkdotnet.org/api/BenchmarkDotNet.Environments.CoreRuntime.html).
[^xctrace]: Apple/Xcode manual mirror, [`xctrace(1)`](https://keith.github.io/xcode-man-pages/xctrace.1.html); also inspect `xcrun xctrace help` from the installed Xcode.
[^wpr]: Microsoft, [Windows Performance Recorder](https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-recorder).
[^wpa]: Microsoft, [Windows Performance Analyzer](https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-analyzer).
[^presentmon]: GameTechDev, [PresentMon console application](https://github.com/GameTechDev/PresentMon/blob/main/README-ConsoleApplication.md).
[^perfview]: Microsoft, [PerfView](https://github.com/microsoft/perfview).
[^pix]: Microsoft, [PIX on Windows](https://devblogs.microsoft.com/pix/).
[^gpuview]: Microsoft, [GPUView](https://learn.microsoft.com/windows-hardware/drivers/display/using-gpuview).
[^windbg]: Microsoft, [WinDbg documentation](https://learn.microsoft.com/windows-hardware/drivers/debugger/).
[^perf-record]: Linux manual pages, [`perf-record(1)`](https://man7.org/linux/man-pages/man1/perf-record.1.html).
[^perf-sched]: Linux manual pages, [`perf-sched(1)`](https://man7.org/linux/man-pages/man1/perf-sched.1.html).
[^bcc]: iovisor, [BCC tools](https://github.com/iovisor/bcc).
[^heaptrack]: KDE, [heaptrack](https://github.com/KDE/heaptrack).
[^valgrind]: Valgrind, [manual](https://valgrind.org/docs/manual/manual.html).
[^renderdoc]: RenderDoc, [documentation](https://renderdoc.org/docs/).
[^nsight]: NVIDIA, [Nsight developer tools](https://developer.nvidia.com/tools-overview).
[^rgp]: AMD, [Radeon GPU Profiler](https://gpuopen.com/rgp/).
[^rmv]: AMD, [Radeon Memory Visualizer](https://gpuopen.com/rmv/).
[^intel-gpa]: Intel, [Graphics Performance Analyzers](https://www.intel.com/content/www/us/en/developer/tools/graphics-performance-analyzers/overview.html).
[^metal-tools]: Apple, [Metal debugging and profiling](https://developer.apple.com/documentation/xcode/metal-debugger).
