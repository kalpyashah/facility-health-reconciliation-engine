import time
from datetime import datetime, timedelta
import random
from src.schemas import NormalizedEvent, EventSource, Subsystem, Severity
from src.reconciliation import ReconciliationEngine


def run_stress_test(num_events: int = 10000):
    print(f"🚀 Generating {num_events:,} synthetic events...")
    
    subsystems = [Subsystem.HVAC, Subsystem.ELECTRICAL, Subsystem.PLUMBING]
    sources = [EventSource.IOT, EventSource.MANUAL, EventSource.CONTRACTOR]
    statuses = ["Normal", "Warning", "Critical", "In-Maintenance"]
    severities = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]

    start_time = datetime(2026, 8, 1, 0, 0, 0)
    events = []

    for i in range(num_events):
        event_time = start_time + timedelta(seconds=random.randint(0, 86400 * 7))
        source = random.choice(sources)
        
        events.append(
            NormalizedEvent(
                event_id=f"STRESS-{i:05d}",
                source=source,
                timestamp=event_time,
                subsystem=random.choice(subsystems),
                status=random.choice(statuses),
                severity=random.choice(severities),
                work_order_id=f"WO-{i}" if source == EventSource.CONTRACTOR else None
            )
        )

    print(f"⚡ Running state reconciliation engine over {num_events:,} events...")
    
    engine_start = time.perf_counter()
    engine = ReconciliationEngine(window_hours=1.0)
    history, audit_logs = engine.reconcile_events(events)
    engine_end = time.perf_counter()

    elapsed = engine_end - engine_start
    print("\n" + "=" * 50)
    print("      PERFORMANCE BENCHMARK RESULTS RESULTS      ")
    print("=" * 50)
    print(f"Total Events Processed:   {num_events:,}")
    print(f"Total Execution Time:    {elapsed:.4f} seconds")
    print(f"Throughput Rate:         {num_events / elapsed:,.2f} events/sec")
    print(f"Audit Traces Generated:  {len(audit_logs):,}")
    print("=" * 50)
    
    assert elapsed < 10.0, "Performance target failed! Processing took longer than 10 seconds."
    print("✅ Benchmark Passed: 10,000 events reconciled well under 10 seconds target!")


if __name__ == "__main__":
    run_stress_test(10000)