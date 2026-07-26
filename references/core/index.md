# Core workflow

Load [`guide.md`](guide.md) first for controlled workload setup, portable .NET triage, managed CPU sampling, heap/dump basics, total-memory ownership, and baseline validation.

## Current command notes

- For standard `dotnet-trace collect`, use `--profile dotnet-common,dotnet-sampled-thread-time` for managed runtime events plus sampled managed stacks. The historical standard profile name `cpu-sampling` was removed.
- `--duration` uses `dd:hh:mm:ss`; use `00:00:00:30` for 30 seconds when portability across current commands matters.
- On Linux and macOS, attach-based .NET diagnostic tools must share the target process `TMPDIR`; otherwise connection can time out.
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
