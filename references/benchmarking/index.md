# .NET benchmarking

Use [`guide.md`](guide.md) for the complete BenchmarkDotNet and application-benchmarking playbook.

## Topic map

- Experiment choice, prerequisites, project setup, lifecycle, inputs, and invalid-benchmark traps: sections 1–8.
- Jobs, runtime configuration, JIT/tiering/PGO, ReadyToRun, single-file, trimming, and NativeAOT: sections 9–11.
- Allocation, disassembly, hardware counters, async, contention, SIMD, and specialized component benchmarks: sections 12 onward.
- Macro, load, soak, startup, UI/GPU, statistical comparison, CI gates, reporting, and validation: later sections of the guide.

## Review corrections and guardrails

- Pin BenchmarkDotNet to a concrete repository-managed version. A wildcard package version is illustrative only and must not be committed.
- Verify runtime constants, toolchains, diagnoser constructors, and command-line options against the pinned BenchmarkDotNet release.
- Run clean timing separately from intrusive diagnosers and external profilers.
- BenchmarkDotNet hardware-counter support is platform- and privilege-dependent; use native tools such as Linux `perf stat` when the built-in diagnoser is unavailable.
- Do not use warmed BenchmarkDotNet microbenchmarks to claim cold-start or first-use improvements. Benchmark published processes for those questions.
- A benchmark must preserve semantic equivalence, ownership, disposal, precision, validation, cancellation, ordering, and concurrency behavior.
- Statistical significance does not imply product significance; define both relative and absolute thresholds.

Load only this domain when implementing or reviewing benchmarks. Add runtime, startup, memory, latency, GPU, and platform references when the benchmark must be tied back to the real application critical path.
