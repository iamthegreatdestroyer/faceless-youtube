"""Performance validation for rate limiter - detailed analysis"""
import time
from src.security.rate_limiter import SlidingWindowRateLimiter

# Create limiter
limiter = SlidingWindowRateLimiter(window_size_seconds=60, max_requests=1000)

# Warm up
for i in range(10):
    limiter.record_request(f"warmup_{i}")

# Single request latency test
latencies = []
for i in range(1000):
    start = time.perf_counter()
    limiter.record_request(f"user_{i % 100}")
    end = time.perf_counter()
    latencies.append((end - start) * 1000)  # Convert to milliseconds

latencies.sort()

# Calculate statistics
avg_latency = sum(latencies) / len(latencies)
p50 = latencies[int(len(latencies) * 0.50)]
p95 = latencies[int(len(latencies) * 0.95)]
p99 = latencies[int(len(latencies) * 0.99)]
max_latency = max(latencies)

print("\n" + "="*60)
print("🚀 RATE LIMITER PERFORMANCE ANALYSIS")
print("="*60)
print(f"\nTest Configuration:")
print(f"  - Window Size: 60 seconds")
print(f"  - Max Requests: 1000")
print(f"  - Test Requests: 1000")
print(f"  - Unique Users: 100")

print(f"\n📊 Latency Results (ms):")
print(f"  Average:     {avg_latency:.4f} ms {'✅ PASS' if avg_latency < 5 else '❌ FAIL'} (target: <5ms)")
print(f"  Median (P50): {p50:.4f} ms")
print(f"  P95:         {p95:.4f} ms")
print(f"  P99:         {p99:.4f} ms")
print(f"  Max:         {max_latency:.4f} ms")

print(f"\n✅ SUCCESS CRITERIA:")
requirements = [
    ("Average latency < 5ms", avg_latency < 5),
    ("P95 latency < 10ms", p95 < 10),
    ("P99 latency < 20ms", p99 < 20),
    ("Max latency < 100ms", max_latency < 100),
]

all_pass = True
for requirement, result in requirements:
    status = "✅" if result else "❌"
    print(f"  {status} {requirement}: {result}")
    if not result:
        all_pass = False

print(f"\n{'='*60}")
print(f"OVERALL: {'🎉 ALL TESTS PASS' if all_pass else '⚠️ SOME TESTS FAILED'}")
print(f"{'='*60}\n")
