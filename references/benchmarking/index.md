# .NET benchmarking

Use [`guide.md`](guide.md) for the complete BenchmarkDotNet and application-benchmarking playbook.

## Topic map

- Experiment choice, prerequisites, project setup, lifecycle, inputs, and invalid-benchmark traps: sections 1–8.
- Jobs, runtime configuration, JIT/tiering/PGO, ReadyToRun, single-file, trimming, and NativeAOT: sections 9–11.
- Allocation, disassembly, hardware counters, async, contention, SIMD, and specialized component benchmarks: sections 12 onward.
- Macro, load, soak, startup, UI/GPU, statistical comparison, CI gates, reporting, and validation: later sections of the guide.

Load only this domain when implementing or reviewing benchmarks; add profiling references when the benchmark must be tied back to an application bottleneck.
