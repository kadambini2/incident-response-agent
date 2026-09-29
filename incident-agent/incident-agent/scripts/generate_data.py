"""Generate ~50 realistic synthetic incidents -> data/incidents.json
Run: python scripts/generate_data.py
Config-push and deploy triggers are deliberately over-represented so Hindsight's
reflect step can surface a real pattern ("most outages follow config pushes").
"""
import json
import pathlib
import random
from datetime import datetime, timedelta, timezone

random.seed(42)

# (trigger, services, severity, symptoms, log, root_cause, fix, minutes_range, weight)
T = [
    ("config push", ["payments-api", "orders-api", "checkout-web"], "SEV1",
     "Requests returning 504 and latency spiked to 30s right after a deploy.",
     "ERROR HikariPool-1 - Connection is not available, request timed out after 30000ms",
     "DB connection pool size reduced in a config change pushed with the deploy.",
     "Rolled back the config to the previous pool size, then redeployed with a load-tested value.", (15, 40), 5),
    ("config push", ["auth-service", "api-gateway"], "SEV2",
     "Spike of 401/403 responses for valid users after config release.",
     "WARN rate limiter: limit=10 req/s exceeded for client, returning 429",
     "Rate limit value mistakenly set to 10 instead of 1000 in a config push.",
     "Reverted the rate limit config and added a validation check for config ranges.", (10, 30), 4),
    ("config push", ["search-service", "recommendation-service"], "SEV2",
     "Search results empty for all queries after config change.",
     "ERROR ElasticsearchException: index 'products_v2' not found",
     "Config push pointed the service to a non-existent index alias.",
     "Restored the index alias in config and reloaded the service.", (12, 35), 3),
    ("deploy", ["orders-api", "inventory-service"], "SEV2",
     "Error rate jumped to 15% immediately after release.",
     "java.lang.NullPointerException at OrderMapper.toDto(OrderMapper.java:88)",
     "New release introduced a null dereference for orders without a shipping address.",
     "Rolled back to the previous release; hotfix added a null check and a regression test.", (20, 60), 4),
    ("deploy", ["checkout-web", "payments-api"], "SEV3",
     "Checkout page slow; p95 latency doubled after release.",
     "WARN N+1 query detected: 412 queries executed for single request",
     "New feature caused an N+1 query pattern on the cart endpoint.",
     "Added eager loading for cart items and released a patch.", (30, 90), 2),
    ("certificate expiry", ["api-gateway", "auth-service"], "SEV1",
     "All HTTPS calls failing with certificate errors.",
     "SSLHandshakeException: PKIX path validation failed: certificate expired",
     "TLS certificate expired because auto-renewal job had been silently failing.",
     "Issued and installed a new certificate manually; fixed the renewal job and added expiry alerts.", (25, 70), 2),
    ("queue lag", ["orders-queue", "notification-service"], "SEV2",
     "Emails and notifications delayed by hours; queue depth growing.",
     "ERROR consumer group 'notifications' lag=482113; rebalance loop detected",
     "Consumer max.poll.interval.ms too low; slow downstream provider caused constant rebalances.",
     "Raised max.poll.interval.ms and reduced batch size; scaled consumers from 3 to 6.", (30, 80), 3),
    ("disk full", ["logging-pipeline", "database-primary"], "SEV1",
     "Writes failing and service unresponsive.",
     "ERROR PANIC: could not write to file: No space left on device",
     "Disk filled up because old WAL/log files were never rotated or cleaned.",
     "Freed space by purging old logs, expanded volume by 200GB, added disk usage alerts at 80%.", (20, 55), 2),
    ("memory leak", ["recommendation-service", "search-service"], "SEV2",
     "Pods restarting every few hours; latency spikes before each restart.",
     "OOMKilled: container exceeded memory limit 2Gi (exit code 137)",
     "Unbounded in-memory cache growth after a caching change.",
     "Added cache size limit and TTL; increased memory limit temporarily and restarted pods.", (40, 120), 2),
    ("dependency outage", ["payments-api", "notification-service"], "SEV2",
     "Payments failing intermittently with upstream errors.",
     "ERROR 503 from stripe-gateway: upstream connect error or disconnect/reset before headers",
     "Third-party provider outage combined with no circuit breaker or retry backoff.",
     "Enabled fallback provider, added circuit breaker and exponential backoff.", (15, 50), 2),
    ("cache", ["auth-service", "api-gateway"], "SEV2",
     "Users randomly logged out; 401 errors on valid tokens.",
     "WARN JWT signature verification failed: key id 'k-rotated' not found",
     "Signing key rotated but one replica still had the old JWKS cached.",
     "Restarted replicas to refresh the JWKS cache and added a 5 minute cache TTL.", (20, 45), 2),
    ("database", ["database-primary", "orders-api"], "SEV1",
     "Slow queries and lock waits; API timing out.",
     "ERROR deadlock detected; process 2211 waits for ShareLock on transaction 88123",
     "Long-running migration held locks on the orders table during peak traffic.",
     "Killed the migration, re-ran it off-peak in smaller batches with lock timeout.", (25, 75), 2),
    ("dns", ["api-gateway", "checkout-web"], "SEV1",
     "Intermittent failures resolving internal service hostnames.",
     "java.net.UnknownHostException: payments-api.internal",
     "CoreDNS pods overloaded after a traffic surge; ndots setting caused excess lookups.",
     "Scaled CoreDNS replicas and tuned ndots and DNS caching.", (30, 90), 1),
]

weights = [t[8] for t in T]
start = datetime(2026, 6, 1, 8, 0, tzinfo=timezone.utc)
out = []
for i in range(50):
    trig, services, sev, sym, log, rc, fix, (lo, hi), _ = random.choices(T, weights)[0]
    ts = start + timedelta(days=i * 1.6 + random.random(), hours=random.randint(0, 12))
    out.append({
        "id": f"INC-{1001 + i}",
        "service": random.choice(services),
        "severity": sev,
        "timestamp": ts.isoformat(),
        "trigger": trig,
        "symptoms": sym,
        "log": log,
        "root_cause": f"[trigger: {trig}] {rc}",
        "fix": fix,
        "outcome": "resolved",
        "minutes_to_resolve": random.randint(lo, hi),
    })

path = pathlib.Path(__file__).resolve().parent.parent / "data" / "incidents.json"
path.write_text(json.dumps(out, indent=2))

from collections import Counter
print(f"Wrote {len(out)} incidents to {path}")
print(Counter(o["trigger"] for o in out))
