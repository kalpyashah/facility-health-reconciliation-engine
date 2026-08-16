from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from src.schemas import NormalizedEvent, EventSource, Severity, SEVERITY_WEIGHT, SOURCE_PRIORITY, AuditDecision


class ReconciliationEngine:
    def __init__(self, window_hours: float = 1.0):
        self.window_hours = window_hours
        self.state_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.audit_log: List[AuditDecision] = []

    def reconcile_events(self, events: List[NormalizedEvent]) -> Tuple[Dict[str, List[Dict[str, Any]]], List[AuditDecision]]:
        """
        Reconstructs subsystem states chronologically and resolves conflicting events.
        Fully deterministic and idempotent.
        """
        if not events:
            return {}, []

        # Step 1: Sort all events chronologically by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Step 2: Group events by subsystem
        subsystem_groups: Dict[str, List[NormalizedEvent]] = defaultdict(list)
        for event in sorted_events:
            subsystem_groups[event.subsystem.value].append(event)

        self.state_history.clear()
        self.audit_log.clear()

        # Step 3: Process each subsystem independently
        for subsystem, sub_events in subsystem_groups.items():
            windows = self._group_into_temporal_windows(sub_events)

            for window_start, window_end, window_events in windows:
                winner, rule_applied, reasoning = self._resolve_window_conflict(window_events)

                # Record state entry
                state_entry = {
                    "subsystem": subsystem,
                    "timestamp": winner.timestamp.isoformat(),
                    "state": winner.status,
                    "severity": winner.severity.value,
                    "controlling_source": winner.source.value,
                    "controlling_event_id": winner.event_id,
                    "work_order_id": winner.work_order_id
                }
                self.state_history[subsystem].append(state_entry)

                # Record auditable decision
                audit = AuditDecision(
                    subsystem=subsystem,
                    window_start=window_start,
                    window_end=window_end,
                    reconciled_state=winner.status,
                    winning_event_id=winner.event_id,
                    winning_source=winner.source.value,
                    rule_applied=rule_applied,
                    reasoning=reasoning,
                    competing_events=[e.event_id for e in window_events]
                )
                self.audit_log.append(audit)

        return dict(self.state_history), self.audit_log

    def _group_into_temporal_windows(self, events: List[NormalizedEvent]) -> List[Tuple[datetime, datetime, List[NormalizedEvent]]]:
        """
        Groups events within a rolling 1-hour window.
        """
        if not events:
            return []

        windows = []
        current_window_events = [events[0]]
        window_start = events[0].timestamp
        window_end = window_start + timedelta(hours=self.window_hours)

        for event in events[1:]:
            if event.timestamp <= window_end:
                current_window_events.append(event)
            else:
                windows.append((window_start, window_end, current_window_events))
                current_window_events = [event]
                window_start = event.timestamp
                window_end = window_start + timedelta(hours=self.window_hours)

        if current_window_events:
            windows.append((window_start, window_end, current_window_events))

        return windows

    def _resolve_window_conflict(self, events: List[NormalizedEvent]) -> Tuple[NormalizedEvent, str, str]:
        """
        Resolves conflicts using source priority hierarchy: Contractor > Manual > IoT.
        Applies deterministic tie-breakers when sources match.
        """
        if len(events) == 1:
            evt = events[0]
            return evt, "Single Event", f"No conflict. State updated via single {evt.source.value} event."

        # Sort by source priority (1 is highest)
        events_by_priority = sorted(events, key=lambda e: e.priority)
        top_priority_level = events_by_priority[0].priority
        top_candidates = [e for e in events_by_priority if e.priority == top_priority_level]

        if len(top_candidates) == 1:
            winner = top_candidates[0]
            competing_sources = set(e.source.value for e in events if e.event_id != winner.event_id)
            rule = f"Source Priority ({winner.source.value} > {', '.join(competing_sources)})"
            reasoning = f"Selected event {winner.event_id} based on superior source authority."
            return winner, rule, reasoning

        # Tie-breaking logic when top priority sources are identical
        source_type = top_candidates[0].source

        if source_type == EventSource.CONTRACTOR:
            # Tie-break 1: Lexicographically higher / later work_order_id, then timestamp
            winner = max(top_candidates, key=lambda e: (e.work_order_id or "", e.timestamp))
            rule = "Tie-Break: Contractor Work Order Precedence"
            reasoning = f"Multiple Contractor updates detected. Selected event {winner.event_id} with work_order_id '{winner.work_order_id}'."
            return winner, rule, reasoning

        elif source_type == EventSource.MANUAL:
            # Tie-break 2: Highest severity, then latest timestamp
            winner = max(top_candidates, key=lambda e: (SEVERITY_WEIGHT[e.severity], e.timestamp))
            rule = "Tie-Break: Manual Inspection Severity Precedence"
            reasoning = f"Multiple Manual reports detected. Selected event {winner.event_id} with highest severity '{winner.severity.value}'."
            return winner, rule, reasoning

        else:  # IoT Telemetry
            # Tie-break 3: Peak severity / latest reading
            winner = max(top_candidates, key=lambda e: (SEVERITY_WEIGHT[e.severity], e.value or 0.0, e.timestamp))
            rule = "Tie-Break: IoT Telemetry Peak Reading"
            reasoning = f"Multiple IoT sensor readings detected. Selected event {winner.event_id} representing peak sensor severity/value."
            return winner, rule, reasoning