# Startup and deployment

Use [`guide.md`](guide.md) for cold start, first request/frame/action, loader behavior, JIT, ReadyToRun, trimming, single-file deployment, NativeAOT, publish size, and deferred first-use regressions. Consult [`../command-reference.md`](../command-reference.md) before executing publish or profiler commands.[^command-reference]

## Review guardrails

- Define explicit milestones such as process start, runtime initialized, services built, window visible, first frame presented, endpoint ready, and first useful operation completed.
- Separate true cold start, OS file-cache effects, warm process behavior, and first-use work.
- Benchmark published artifacts rather than `dotnet run` when deployment shape is under comparison.
- Record architecture, RID, self-contained/framework-dependent state, ReadyToRun, trimming, single-file extraction behavior, AOT, globalization, symbols, and environment overrides.
- An apparent startup improvement that moves work into the first request, first frame, first interaction, or background queue is deferral—not removal.
- Validate compatibility, diagnostics, code size, memory, throughput, and steady-state performance alongside startup.

Pair this guide with [`../runtime/index.md`](../runtime/index.md), [`../benchmarking/index.md`](../benchmarking/index.md), and the relevant [`../platforms/index.md`](../platforms/index.md) documents.

## Documentation footnotes

[^command-reference]: [`../command-reference.md`](../command-reference.md).
[^publish]: Microsoft, [`dotnet publish`](https://learn.microsoft.com/dotnet/core/tools/dotnet-publish).
[^r2r]: Microsoft, [ReadyToRun deployment](https://learn.microsoft.com/dotnet/core/deploying/ready-to-run).
[^single-file]: Microsoft, [single-file deployment](https://learn.microsoft.com/dotnet/core/deploying/single-file/overview).
[^trimming]: Microsoft, [trim self-contained deployments](https://learn.microsoft.com/dotnet/core/deploying/trimming/trim-self-contained).
[^nativeaot]: Microsoft, [Native AOT deployment](https://learn.microsoft.com/dotnet/core/deploying/native-aot/).
[^dotnet-trace]: Microsoft, [`dotnet-trace`](https://learn.microsoft.com/dotnet/core/diagnostics/dotnet-trace).