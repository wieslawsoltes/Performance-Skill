# Managed runtime

Use [`guide.md`](guide.md) for managed CPU, runtime events, allocation, GC, JIT/tiering/PGO, exceptions, ThreadPool scheduling, contention, async investigations, dumps, and SOS.

## Current command notes

- Standard `dotnet-trace collect` managed sampling uses `--profile dotnet-common,dotnet-sampled-thread-time`.
- The historical `cpu-sampling` standard profile was removed. Do not use it with `dotnet-trace collect` unless the installed tool explicitly documents compatibility.
- Linux `dotnet-trace collect-linux` is a separate preview workflow where `cpu-sampling` is a valid perf-based profile.
- Query `dotnet-trace collect --help` and record the tool/runtime versions before using provider masks or profile names.
- On Linux and macOS, ensure the tool and target share `TMPDIR` for PID/name attachment.
- Prefer the raw `.nettrace` for event analysis; Speedscope conversion is useful for stacks but does not preserve every event type.

Pair this domain with:

- [`../memory/index.md`](../memory/index.md) when allocation traffic may become retention or total-process growth;
- [`../latency/index.md`](../latency/index.md) for starvation, off-CPU delay, queues, and dependencies;
- [`../startup/index.md`](../startup/index.md) for cold JIT, loader, ReadyToRun, and first-use behavior;
- [`../platforms/index.md`](../platforms/index.md) for native stacks, scheduling, kernel, I/O, and system-wide evidence.
