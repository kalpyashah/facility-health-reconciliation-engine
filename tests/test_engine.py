import pytest
from datetime import datetime
from src.schemas import NormalizedEvent, EventSource, Subsystem, Severity
from src.ingestion import EventIngestor
from src.reconciliation import ReconciliationEngine


def test_source_priority_contractor_over_manual():
    e1 = NormalizedEvent(
        event_id="E1", source=EventSource.MANUAL,
        timestamp=datetime.fromisoformat("2026-08-16T08:00:00"),
        subsystem=Subsystem.ELECTRICAL, status="Critical", severity=Severity.HIGH
    )
    e2 = NormalizedEvent(
        event_id="E2", source=EventSource.CONTRACTOR,
        timestamp=datetime.fromisoformat("2026-08-16T08:15:00"),
        subsystem=Subsystem.ELECTRICAL, status="Normal", severity=Severity.LOW,
        work_order_id="WO-101"
    )

    engine = ReconciliationEngine(window_hours=1.0)
    history, audit = engine.reconcile_events([e1, e2])

    assert history["Electrical"][0]["state"] == "Normal"
    assert history["Electrical"][0]["controlling_source"] == "Contractor"
    assert audit[0].winning_event_id == "E2"


def test_duplicate_manual_reports_severity_tiebreak():
    e1 = NormalizedEvent(
        event_id="M1", source=EventSource.MANUAL,
        timestamp=datetime.fromisoformat("2026-08-16T08:30:00"),
        subsystem=Subsystem.PLUMBING, status="Warning", severity=Severity.MEDIUM, user_id="USR-1"
    )
    e2 = NormalizedEvent(
        event_id="M2", source=EventSource.MANUAL,
        timestamp=datetime.fromisoformat("2026-08-16T08:30:00"),
        subsystem=Subsystem.PLUMBING, status="Critical", severity=Severity.HIGH, user_id="USR-2"
    )

    engine = ReconciliationEngine(window_hours=1.0)
    history, audit = engine.reconcile_events([e1, e2])

    assert history["Plumbing"][0]["state"] == "Critical"
    assert audit[0].winning_event_id == "M2"


def test_malformed_event_skipping():
    ingestor = EventIngestor()
    events, stats = ingestor.parse_csv("data/fixtures/sample_events.csv")
    assert stats["skipped_rows"] >= 1


def test_determinism_replay():
    ingestor = EventIngestor()
    events1, _ = ingestor.parse_csv("data/fixtures/sample_events.csv")
    engine1 = ReconciliationEngine()
    history1, _ = engine1.reconcile_events(events1)

    ingestor2 = EventIngestor()
    events2, _ = ingestor2.parse_csv("data/fixtures/sample_events.csv")
    engine2 = ReconciliationEngine()
    history2, _ = engine2.reconcile_events(events2)

    assert history1 == history2