# Managed, native, virtual, and GPU memory profiling

Use this reference when memory grows, allocation rate is high, the process is killed under pressure, or managed heap metrics do not explain RSS/working-set growth.

## Build a memory ownership ledger

Record the same timestamps for:

- managed live bytes;
- committed GC heap;
- LOH and pinned-object data where available;
- process working set/RSS;
- private/dirty memory;
- committed and reserved virtual memory;
- native allocator bytes;
- mapped files;
- executable/JIT/loader mappings;
- graphics allocations and GPU residency;
- container/cgroup memory current, high-water mark, and limit.

Do not assign ownership from one metric.

## Reproduction sequence

For growth investigations capture at least these points:

1. process start;
2. after warm-up;
3. before suspect workload;
4. after N repetitions;
5. after idle/drain;
6. after explicit cleanup and full GC only when the experiment requires it;
7. after another N repetitions.

Use the same workload count at every comparison point. Record wall-clock time because caches and delayed-release queues may be time-based.

## Managed heap snapshots

```bash
mkdir -p artifacts/performance/memory

dotnet-gcdump collect \
  --process-id <PID> \
  --output artifacts/performance/memory/heap-before.gcdump

# execute the deterministic workload N times

dotnet-gcdump collect \
  --process-id <PID> \
  --output artifacts/performance/memory/heap-after.gcdump

dotnet-gcdump report artifacts/performance/memory/heap-before.gcdump \
  > artifacts/performance/memory/heap-before.txt

dotnet-gcdump report artifacts/performance/memory/heap-after.gcdump \
  > artifacts/performance/memory/heap-after.txt
```

Compare type count and retained bytes, but remember that `gcdump` collection changes process state and can require substantial temporary memory.

## Full-dump retention analysis

Use a full dump when type statistics are insufficient.

```bash
dotnet-dump collect \
  --process-id <PID> \
  --type Full \
  --output artifacts/performance/memory/process.dmp

dotnet-dump analyze artifacts/performance/memory/process.dmp
```

Suggested sequence:

```text
eeheap -gc
dumpheap -stat
dumpheap -type Namespace.SuspectType
gcroot <object-address>
gchandles
finalizequeue
```

For each suspect type establish:

- count and total size;
- expected ownership and lifetime;
- dominant root path;
- whether roots are static fields, events, caches, timers, tasks, thread locals, handles, finalizer queues, interop wrappers, or framework retention;
- whether the graph is bounded by design.

## Managed retention patterns

Check explicitly for:

- event subscriptions not removed;
- static dictionaries and unbounded caches;
- timers and callbacks retaining state;
- incomplete tasks and cancellation registrations;
- `AsyncLocal` and execution-context retention;
- closures capturing large graphs;
- dispatcher queues retaining controls or documents;
- pooled objects never returned;
- finalizable objects accumulating;
- pinned arrays and native interop handles;
- image, font, geometry, texture, and document caches;
- weak-reference caches whose values or keys are still strongly retained elsewhere.

## Allocation pressure without retention

When live heap is stable but allocation is high, collect sampled allocation stacks and classify:

- strings and formatting;
- arrays and buffers;
- boxing and interface dispatch helpers;
- LINQ iterators and enumerators;
- closures/delegates;
- async state machines and tasks;
- reflection metadata and dynamic code;
- serializers/parsers;
- temporary graphics/path/text objects;
- P/Invoke marshalling buffers.

Validate allocation reductions against CPU and tail latency. Pooling can lower allocation while increasing retention, contention, fragmentation, and stale-data risk.

## LOH, pinning, fragmentation, and finalization

Investigate:

- repeated allocations above the LOH threshold;
- large arrays resized or recreated;
- pinned buffers preventing compaction;
- native APIs holding managed pins longer than expected;
- finalizers blocked behind one slow finalizer;
- disposable wrappers relying on finalization;
- heap committed bytes remaining high after live bytes fall;
- address-space fragmentation in long-running processes.

Do not force full GC in production as a general fix. Use it only as a controlled diagnostic experiment or where the application model explicitly supports it.

## Native-memory escalation

Escalate when managed live bytes remain stable but private/RSS/commit grows.

Potential owners:

- `malloc`/native heap allocations;
- C/C++ object graphs;
- Objective-C/CoreFoundation objects;
- COM objects;
- memory-mapped files;
- decompression/codec libraries;
- Skia, Cairo, FreeType, HarfBuzz, WebGPU/wgpu-native, Vulkan, Metal, Direct3D;
- thread stacks and TLS;
- JIT/code heaps;
- allocator arenas and fragmentation;
- delayed resource destruction awaiting fences;
- driver-private allocations.

Use the platform reference for native heap and VM tools. Capture allocation stacks if possible; totals without stacks rarely identify ownership.

## Interop ownership audit

For every native handle or pointer document:

- creator;
- owning managed wrapper;
- transfer/borrow semantics;
- release API;
- thread-affinity requirements;
- whether release is immediate or deferred;
- behavior on exceptions and cancellation;
- behavior during device loss or shutdown;
- whether finalization exists only as a safety net.

Search for all creation paths, including resize, retry, fallback, and error handling—not only the normal path.

## GPU and graphics memory

Correlate process memory with graphics-tool evidence for:

- textures, buffers, render targets, depth/stencil images;
- swapchain/drawable images;
- upload/readback/staging pools;
- shader and pipeline caches;
- descriptor/bind-group pools;
- glyph atlases and image caches;
- transient render graphs;
- allocator heap/block overhead;
- resident versus allocated bytes;
- deferred destruction queues;
- compositor-owned surfaces.

Stable managed wrappers do not prove stable native/GPU allocations. Conversely, growing managed wrapper count does not prove resources remain resident after release.

## Mapped files and page cache

Distinguish mappings from private heap:

- file-backed versus anonymous;
- shared versus private;
- resident versus merely mapped;
- clean versus dirty;
- page-cache effects;
- copy-on-write growth;
- memory-mapped database or asset behavior.

A large virtual mapping is not itself a leak. Determine whether committed/resident/private pages grow and whether the mapping is bounded.

## Containers and memory limits

Record:

- container memory limit;
- current usage and peak;
- swap configuration;
- OOM-kill evidence;
- process RSS/PSS/private data;
- managed heap hard-limit configuration;
- sidecar/profiler overhead.

A process can be healthy on the host yet fail inside a cgroup because the GC, native libraries, page cache, and profiler compete under the container limit.

## Differential analysis

Create a table per capture point:

```text
Point        Live GC   GC committed   Private/RSS   Native heap   GPU resident   Notes
start        ...       ...            ...           ...           ...            ...
warm         ...       ...            ...           ...           ...            ...
after N      ...       ...            ...           ...           ...            ...
after idle   ...       ...            ...           ...           ...            ...
after clean  ...       ...            ...           ...           ...            ...
```

Classify the shape:

- monotonic unbounded growth;
- step growth followed by plateau;
- sawtooth allocation/collection;
- delayed release after GPU/IO completion;
- cache warm-up;
- allocator high-water behavior;
- fragmentation;
- periodic leak tied to one operation.

## Validation

After the fix, repeat the identical sequence and report:

- slope per operation and per minute;
- plateau size after warm-up;
- live managed bytes and dominant retained types;
- private/RSS/PSS and commit;
- native allocation totals and hottest allocation stacks;
- GPU allocated/resident bytes;
- cleanup/drain latency;
- performance impact of the lifetime change.

Do not call a problem fixed because memory drops once. Prove bounded behavior across enough repetitions and idle/drain cycles.