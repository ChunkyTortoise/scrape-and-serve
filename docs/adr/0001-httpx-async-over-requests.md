# ADR 0001: httpx Async Over requests

## Status
Accepted

## Context
The scraping system needs to fetch many URLs concurrently without blocking. The popular `requests` library is synchronous, meaning each HTTP call blocks the thread until completion. For high-volume scraping, this creates a bottleneck where throughput is limited by sequential execution or expensive thread pools.

## Decision
Use `httpx` with async/await for all HTTP operations. Leverage connection pooling to reuse TCP connections across requests to the same host. Use `asyncio.gather()` for concurrent URL fetching with configurable concurrency limits to avoid overwhelming target servers.

## Consequences
- **Positive**: Achieves 5-10x throughput improvement over synchronous requests. Efficient resource usage with a single event loop handling thousands of concurrent connections. Connection pooling reduces TCP handshake overhead.
- **Negative**: Requires async-aware code throughout the scraping pipeline. Debugging async code is harder than synchronous equivalents (stack traces, exception handling). Third-party libraries must be async-compatible or wrapped in executor calls.
