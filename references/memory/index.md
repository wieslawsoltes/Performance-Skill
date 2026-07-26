# Memory

Use [`guide.md`](guide.md) for managed, native, virtual-memory, mapped-file, graphics, and GPU-memory ownership.

## Review guardrails

- Compare equivalent lifecycle points: before warm-up, after warm-up, after repeated workload, after drain/idle, and after explicit cleanup.
- Separate allocation traffic from retention, reserved address space from committed memory, and committed memory from resident/private memory.
- Correlate managed live bytes with process private/RSS/PSS, native allocator growth, mappings, handles, graphics resources, and GPU residency.
- Do not force full GCs merely to make production graphs look cleaner; record every intrusive action and its effect.
- Account for pooling, caches, deferred destruction, finalization, pinned objects, interop wrappers, compositor surfaces, and allocator fragmentation.
- Treat dumps and heap artifacts as sensitive data.

Pair this guide with [`../runtime/index.md`](../runtime/index.md) for managed retention, [`../gpu/index.md`](../gpu/index.md) for graphics resources, and [`../platforms/index.md`](../platforms/index.md) for native/VM ownership.
