from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
import json
from src.schemas import RawEvent, NormalizedEvent, EventSource, Subsystem, Severity
from src.ingestion import EventIngestor
from src.reconciliation import ReconciliationEngine
from src.audit import AuditExporter

app = FastAPI(
    title="Facility Health Reconciliation Engine API",
    description="Real-time event ingestion, state reconstruction, and conflict resolution service",
    version="1.0.0"
)

# Global in-memory engine state
ingestor = EventIngestor()
engine = ReconciliationEngine(window_hours=1.0)
all_events: List[NormalizedEvent] = []


@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "Facility Health Reconciliation Engine",
        "processed_events_count": len(all_events)
    }


@app.post("/events", status_code=status.HTTP_200_OK)
def ingest_and_reconcile_events(payload: List[Dict[str, Any]]):
    """
    Accepts JSON array of event objects, validates schemas, reconciles states, and returns audit output.
    """
    global all_events
    if not payload:
        raise HTTPException(status_code=400, detail="Empty event payload provided")

    new_events, stats = ingestor.parse_json_payload(payload)

    if not new_events and stats["skipped_items"] > 0:
        raise HTTPException(status_code=400, detail=f"All events malformed or invalid: {stats['errors']}")

    all_events.extend(new_events)
    state_history, audit_logs = engine.reconcile_events(all_events)

    # Automatically save outputs
    os.makedirs("data/outputs", exist_ok=True)
    AuditExporter.export_json(audit_logs, "data/outputs/audit_trail.json")
    AuditExporter.export_state_history(state_history, "data/outputs/reconciled_state.json")

    return {
        "status": "success",
        "ingested_count": len(new_events),
        "skipped_count": stats["skipped_items"],
        "reconciled_subsystems": list(state_history.keys()),
        "audit_decisions_count": len(audit_logs)
    }


@app.get("/state/{subsystem}")
def get_subsystem_state(subsystem: str):
    """
    Returns current and historical state trace for a specific subsystem (HVAC, Electrical, Plumbing).
    """
    subsystem_upper = subsystem.strip().upper()
    state_history, _ = engine.reconcile_events(all_events)

    if subsystem_upper not in state_history:
        raise HTTPException(status_code=404, detail=f"Subsystem '{subsystem_upper}' not found or no events processed yet.")

    return {
        "subsystem": subsystem_upper,
        "history": state_history[subsystem_upper],
        "current_state": state_history[subsystem_upper][-1] if state_history[subsystem_upper] else None
    }


@app.get("/audit")
def get_audit_trail():
    """
    Returns explainable audit trail decision log.
    """
    _, audit_logs = engine.reconcile_events(all_events)
    return [
        {
            "subsystem": log.subsystem,
            "window_start": log.window_start.isoformat(),
            "window_end": log.window_end.isoformat(),
            "reconciled_state": log.reconciled_state,
            "winning_event_id": log.winning_event_id,
            "winning_source": log.winning_source,
            "rule_applied": log.rule_applied,
            "reasoning": log.reasoning,
            "competing_events": log.competing_events
        }
        for log in audit_logs
    ]