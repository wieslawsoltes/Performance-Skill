# Startup, deployment model, JIT, ReadyToRun, trimming, and NativeAOT

Use this reference for cold-start latency, first-interaction stalls, short-lived tools, service activation, application size, deployment-model comparisons, and initialization regressions.

## Define startup milestones

Do not measure only process start to `Main`. Instrument milestones relevant to the user:

```text
process created
runtime initialized
managed entry point
DI/container built
configuration loaded
first window created
first layout completed
first frame submitted
first frame presented
server listening
first request accepted
first successful response
background initialization complete
```

Use stable event names and monotonic timestamps. For UI, first presented frame is usually more meaningful than constructor completion.

## Cold, warm, and first-use scenarios

Measure separately:

- cold OS/filesystem cache where practical;
- warm filesystem cache but new process;
- first process after installation/update;
- first use of a feature that triggers JIT, shader compilation, font loading, database initialization, or lazy dependency construction;
- subsequent steady-state launch.

Do not claim cold-start improvements from warm-cache runs.

## Launch through collectors

EventPipe startup trace:

```bash
mkdir -p artifacts/performance/startup

dotnet-trace collect \
  --show-child-io \
  --output artifacts/performance/startup/startup.nettrace \
  -- dotnet exec ./App.dll
```

Platform-native launch traces are required when loader, filesystem, native libraries, code signing, antivirus, dynamic linker, graphics driver, compositor, or process scheduling contribute.

Use the platform documents for:

- macOS `xctrace --launch`;
- Windows WPR/WPA, PerfView, and process-lifetime filtering;
- Linux `perf record -- ./App`, `strace` where justified, and page-fault/loader evidence.

## Startup ownership breakdown

Classify time into:

- process and runtime initialization;
- module and native-library loading;
- assembly loading;
- metadata and reflection;
- JIT compilation and tiering;
- static constructors/module initializers;
- dependency-injection graph construction;
- configuration, JSON/XML, and environment access;
- file and database I/O;
- font/image/theme/resource loading;
- shader/pipeline creation;
- window system and compositor initialization;
- first layout and first render;
- synchronous network calls;
- background work accidentally awaited on the critical path.

## Loader and assembly analysis

Record:

- assembly/module load count;
- load order and timestamps;
- probing failures;
- satellite/resource assembly loads;
- dynamic assembly generation;
- reflection scans;
- plugin discovery;
- native dependency resolution;
- single-file extraction or mapping behavior where applicable.

Search for broad assembly scans, repeated `Assembly.GetTypes`, reflection-based registration, plugin probing across large directories, and unnecessary eager loading.

## Static initialization

Use stacks and timeline markers to identify expensive:

- static constructors;
- singleton factories;
- serializer metadata construction;
- regex compilation;
- font and graphics initialization;
- native library initialization;
- cache population.

Move work off the startup critical path only if lifetime, ordering, error propagation, and first-use latency remain acceptable.

## JIT and tiering

Capture JIT events and compare:

- total JIT time;
- method count and code size;
- generic instantiation;
- first-call latency;
- tier transitions after launch;
- methods falling back from ReadyToRun;
- dynamic-code generation.

Warm startup can improve while first-interaction latency worsens if compilation is merely deferred. Include first-use scenarios in validation.

## ReadyToRun experiment

```bash
dotnet publish -c Release -r <RID> \
  -p:PublishReadyToRun=true \
  -p:PublishReadyToRunComposite=true
```

Record output size, publish time, startup, working set, warm throughput, and whether JIT still occurs. ReadyToRun can trade size and code quality for lower startup compilation; prove the trade-off for the real workload.

## Trimming and single-file deployment

```bash
dotnet publish -c Release -r <RID> \
  -p:PublishTrimmed=true \
  -p:PublishSingleFile=true
```

Treat trimming warnings as correctness risks. Validate reflection, serializers, XAML/resource loading, plugins, native libraries, and dynamic activation.

For single-file deployment distinguish mapping versus extraction behavior and test on the actual target OS/filesystem/security configuration.

## NativeAOT experiment

```bash
dotnet publish -c Release -r <RID> -p:PublishAot=true
```

Compare:

- cold and warm startup;
- first operation latency;
- binary size;
- RSS/private memory;
- steady-state throughput;
- diagnostics availability;
- native symbol quality;
- reflection/dynamic-code compatibility;
- build time and portability.

NativeAOT removes runtime JIT but does not automatically remove application initialization, I/O, native-library, shader, or compositor costs. Diagnose the published NativeAOT artifact with native platform tools and its supported diagnostics.

## ASP.NET Core/service readiness

Instrument separately:

- host build;
- configuration and secrets providers;
- logging initialization;
- service-provider construction;
- hosted-service startup;
- endpoint binding;
- readiness probe success;
- first request and first successful response.

Do not mark ready before required initialization is complete. Conversely, move optional warm-up after readiness only if requests remain correct and latency objectives are met.

## UI first frame

For Avalonia, WPF, WinUI, MAUI, Skia, WebGPU, and custom UI stacks capture:

- application entry;
- window creation;
- native surface creation;
- theme/style/resource loading;
- first measure/arrange;
- text/font initialization;
- renderer/device creation;
- shader/pipeline compilation;
- first command submission;
- drawable/swapchain acquisition;
- first present.

A blank window shown early is not necessarily a startup improvement if time-to-usable-content or first-input responsiveness regresses.

## Statistical collection

Automate multiple fresh-process launches. Record each milestone as a separate sample. Avoid measuring the launch script or build command as application startup.

Report median, p90/p95 where sample count permits, minimum only as diagnostic context, and environmental variance. Reboot/cache-drop experiments can be invasive and platform-specific; document exactly what was done.

## Validation matrix

```text
Deployment      Cold start   Warm start   First action   Size   RSS   Throughput   Diagnostics
FDD/JIT         ...          ...          ...            ...    ...   ...          ...
R2R             ...          ...          ...            ...    ...   ...          ...
Trimmed         ...          ...          ...            ...    ...   ...          ...
Single-file     ...          ...          ...            ...    ...   ...          ...
NativeAOT       ...          ...          ...            ...    ...   ...          ...
```

Use the deployment form intended for production as the final validation target. A faster synthetic launch is not sufficient if compatibility, steady-state performance, memory, diagnostics, or update size regresses.