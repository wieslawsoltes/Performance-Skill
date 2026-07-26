# Core workflow

Load [`guide.md`](guide.md) first for controlled workload setup, portable .NET triage, managed CPU sampling, heap/dump basics, total-memory ownership, and baseline validation.

Use the verified [`../command-reference.md`](../command-reference.md) before executing copied commands.[^command-reference]

## Current command notes

- For standard `dotnet-trace collect`, use `--profile dotnet-common,dotnet-sampled-thread-time` for managed runtime events plus sampled managed stacks. The historical standard profile name `cpu-sampling` was removed.[^dotnet-trace]
- `--duration` uses `dd:hh:mm:ss`; `00:00:00:30` is the unambiguous 30-second form.[^dotnet-trace]
- On Linux and macOS, attach-based .NET diagnostic tools must share the target process `TMPDIR`; otherwise connection can time out.[^dotnet-trace][^dotnet-counters]
- Preserve `.nettrace` as the source artifact even when exporting Speedscope or reports.

Then load only the domain index required by the evidence:

- [`../runtime/index.md`](../runtime/index.md)
- [`../memory/index.md`](../memory/index.md)
- [`../latency/index.md`](../latency/index.md)
- [`../startup/index.md`](../startup/index.md)
- [`../benchmarking/index.md`](../benchmarking/index.md)
- [`../production/index.md`](../production/index.md)
- [`../gpu/index.md`](../gpu/index.md)
- [`../platforms/index.md`](../platforms/index.md)

## Documentation footnotes

[^command-reference]: [`../command-reference.md`](../command-reference.md).
[^dotnet-trace]: Microsoft, [`dotnet-trace`](https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-trace).
[^dotnet-counters]: Microsoft, [`dotnet-counters`](https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-counters).