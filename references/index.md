# Reference map

Use this file as the package-level reference router. Begin with [`core/index.md`](core/index.md), then load only the domains and platforms required by the current hypothesis.

## Domains

- [`core/index.md`](core/index.md) — experiment setup, portable first-pass triage, artifact conventions, and validation baseline.
- [`runtime/index.md`](runtime/index.md) — managed CPU, EventPipe, allocation, GC, JIT, exceptions, ThreadPool, locks, async stacks, dumps, and SOS.
- [`memory/index.md`](memory/index.md) — managed, native, virtual, mapped, graphics, and GPU-memory ownership.
- [`latency/index.md`](latency/index.md) — contention, queues, backpressure, timers, file/network/database I/O, distributed tracing, and dispatcher latency.
- [`startup/index.md`](startup/index.md) — cold start, first use, loader, ReadyToRun, trimming, single-file, and NativeAOT.
- [`benchmarking/index.md`](benchmarking/index.md) — BenchmarkDotNet and application-level micro, component, macro, load, and soak experiments.
- [`production/index.md`](production/index.md) — bounded production collection, diagnostic ports, containers, Kubernetes, permissions, privacy, and retention.
- [`gpu/index.md`](gpu/index.md) — rendering, GPU timelines, timestamps, queues, shaders, resources, WebGPU, compositor, and presentation.

## Platforms

Use [`platforms/index.md`](platforms/index.md) to choose every applicable native/system guide. Most single-host investigations use one platform guide; cross-platform comparisons, distributed systems, remote rendering, or client/server workflows may require several.

## Version-sensitive command policy

Tool syntax changes. Before executing commands:

1. record the installed tool version;
2. query `--help`, installed profiles, templates, or capabilities;
3. prefer current official profile names;
4. keep the raw artifact and exact command beside the result;
5. document deviations from examples in these references.

Current important correction: standard `dotnet-trace collect` uses `dotnet-sampled-thread-time` for managed stack sampling. The historical `cpu-sampling` profile was removed from standard collection; `cpu-sampling` remains valid for the separate Linux `collect-linux` perf-based workflow.
