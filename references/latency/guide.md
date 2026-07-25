# Concurrency, async, I/O, networking, and latency profiling

Use this reference when CPU is not the whole story: requests are slow with modest CPU, threads block, UI stalls, queueing grows, throughput collapses under concurrency, or external dependencies dominate.

## Build a latency budget

Split end-to-end latency into explicit stages:

```text
arrival/dispatch
queue wait
application CPU
lock/semaphore wait
ThreadPool scheduling delay
DNS/connect/TLS
request write
remote-service/database latency
response read
serialization/deserialization
UI/compositor handoff
completion/presentation
```

Instrument stage boundaries with stable request or operation identifiers. A trace without correlation IDs may show activity but not the critical path of one slow operation.

## Controlled load

Record:

- concurrency and arrival model;
- warm-up duration;
- request/operation count;
- payload and data-set size;
- connection-pool state;
- cache state;
- timeout/retry policy;
- machine and container limits;
- downstream dependency state.

Use a load generator appropriate to the protocol and store its raw latency output. Compare throughput and p50/p90/p95/p99/max, not averages alone.

## ThreadPool starvation triage

Collect `System.Runtime` counters and repeated stacks.

```bash
dotnet-counters collect \
  --process-id <PID> \
  --refresh-interval 1 \
  --format csv \
  --output artifacts/performance/concurrency/counters.csv \
  --counters System.Runtime

for i in 1 2 3 4 5; do
  dotnet-stack report --process-id <PID> \
    > "artifacts/performance/concurrency/stacks-$i.txt"
  sleep 1
done
```

Evidence of starvation often includes rising queue length, slowly increasing worker count, low-to-moderate CPU, and repeated blocking stacks.

Search for:

- `.Result`, `.Wait()`, synchronous `GetAwaiter().GetResult()`;
- synchronous file/network/database calls inside request paths;
- blocking locks held across awaits or external calls;
- synchronous logging sinks;
- bounded scheduler or dispatcher saturation;
- long-running work incorrectly placed on ThreadPool workers.

Do not treat increasing minimum worker threads as the primary fix until blocking ownership is understood. It can mask starvation while increasing contention and memory.

## Lock and semaphore investigations

Collect runtime contention events and platform context-switch/wait evidence. For each hotspot establish:

- synchronization primitive;
- owner stack;
- waiter stacks;
- hold time;
- wait time distribution;
- contention count;
- protected work;
- whether external I/O occurs while held;
- lock ordering and reentrancy;
- fairness/convoy behavior.

Typical fixes include reducing critical-section scope, partitioning state, immutable snapshots, lock-free read paths, batching, or moving slow work outside the lock. Validate correctness under stress and cancellation.

## Async critical-path analysis

Track logical operations, not only physical threads.

Instrument with `Activity`, distributed tracing, EventSource, or framework spans. Include:

- operation name;
- trace/span identifier;
- parent relationship;
- queue-enter and queue-leave timestamps;
- dependency name;
- retry number;
- timeout/cancellation reason;
- completion status.

Investigate:

- serial awaits that could safely overlap;
- accidental fan-out and unbounded parallelism;
- excessive `Task.Run`;
- continuations captured to a busy UI synchronization context;
- async locks with long holders;
- cancellation registration churn;
- incomplete tasks retaining state;
- channels/queues with no backpressure;
- producer/consumer imbalance.

## Queues and backpressure

Measure per queue:

- depth and high-water mark;
- enqueue/dequeue rate;
- queue-wait distribution;
- rejection/drop count;
- consumer utilization;
- batch size;
- age of oldest item;
- memory retained by queued payloads.

A bounded queue protects memory but can move the symptom to producer latency or rejection. Report both sides.

## Timer, polling, and wakeup cost

Use platform scheduler traces to find excessive wakeups. Check:

- short periodic timers;
- polling loops;
- spin waits;
- many independent timers that could be coalesced;
- UI invalidation timers;
- retry loops without jitter/backoff;
- idle connections or keepalive intervals.

Measure useful work per wakeup and impact on power, CPU residency, and frame pacing.

## File I/O

Correlate application spans with platform file-system traces.

Measure:

- operation count and bytes;
- synchronous versus asynchronous API use;
- queueing and service time;
- cache hits versus physical disk activity;
- metadata calls and directory enumeration;
- flush/fsync frequency;
- small fragmented reads/writes;
- memory mapping and page faults;
- antivirus/indexer or other-process interference on Windows;
- network-filesystem behavior.

A high-level `ReadAsync` duration does not prove disk latency; time may be spent in queueing, locks, decoding, allocation, or downstream processing.

## Network and HTTP

Capture:

- DNS duration;
- connect duration;
- TLS handshake duration;
- connection-pool wait;
- request-header/body write;
- server time to first byte;
- response body read;
- HTTP version and connection reuse;
- retry and redirect counts;
- socket errors and retransmissions.

Inspect for:

- creating `HttpClient`/handlers per request;
- connection exhaustion;
- low per-server connection limits;
- stale DNS assumptions;
- proxy behavior;
- HTTP/2 stream limits or head-of-line effects;
- HTTP/3/QUIC fallback;
- synchronous serialization;
- large response buffering;
- cancellation that leaves expensive downstream work running.

Use packet capture only when permitted and necessary; protect credentials and payload data.

## Database calls

Record command spans with normalized statement identity, duration, row count, connection-pool wait, transaction scope, and retry count. Avoid logging secrets or full sensitive SQL parameters.

Investigate:

- N+1 query patterns;
- serial independent queries;
- connection-pool saturation;
- long transactions;
- lock waits and deadlocks;
- missing indexes or poor plans;
- excessive materialization;
- client-side filtering;
- retry amplification;
- sync database APIs in async request paths.

Application traces identify where time is lost; database-native tools are required to prove engine-side causes.

## UI and dispatcher latency

For UI applications instrument:

- input event timestamp;
- dispatcher enqueue/dequeue;
- command/view-model work;
- binding updates;
- layout/invalidation;
- render submission;
- present.

Check for:

- long synchronous handlers;
- high-priority dispatcher flooding;
- background work marshalled too frequently to UI;
- synchronous waits on render or worker threads;
- collection change storms;
- excessive property notifications;
- timers/polling invalidating unchanged content.

Correlate with the GPU reference when the stall crosses the rendering boundary.

## Distributed systems

For multi-service latency, use trace context end to end. Report:

- service time per span;
- queue time where available;
- network gaps;
- retries and hedged requests;
- fan-out width;
- critical-path versus parallel noncritical spans;
- clock-synchronization limitations.

The sum of all span durations can exceed wall latency because spans overlap. Optimize the critical path, not the largest aggregate total alone.

## Validation under load

After a fix, repeat the same arrival pattern and report:

- throughput;
- p50/p90/p95/p99/max latency;
- queue-wait p95/p99;
- ThreadPool queue and worker count;
- lock wait and hold distributions;
- dependency latency and connection-pool wait;
- timeout, cancellation, retry, and error rates;
- CPU, allocation, GC, and memory;
- fairness and behavior during overload.

Validate graceful degradation: bounded queues, explicit rejection, cancellation propagation, and recovery after the load stops.