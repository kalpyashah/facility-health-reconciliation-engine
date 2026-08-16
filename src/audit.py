import json
import csv
from typing import List, Dict, Any
from src.schemas import AuditDecision


class AuditExporter:
    @staticmethod
    def export_json(audit_logs: List[AuditDecision], output_path: str) -> None:
        """
        Exports decision trace audit logs to a formatted JSON file.
        """
        data = [
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

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def export_csv(audit_logs: List[AuditDecision], output_path: str) -> None:
        """
        Exports decision trace audit logs to CSV format.
        """
        fieldnames = [
            "subsystem", "window_start", "window_end", "reconciled_state",
            "winning_event_id", "winning_source", "rule_applied",
            "reasoning", "competing_events"
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for log in audit_logs:
                writer.writerow({
                    "subsystem": log.subsystem,
                    "window_start": log.window_start.isoformat(),
                    "window_end": log.window_end.isoformat(),
                    "reconciled_state": log.reconciled_state,
                    "winning_event_id": log.winning_event_id,
                    "winning_source": log.winning_source,
                    "rule_applied": log.rule_applied,
                    "reasoning": log.reasoning,
                    "competing_events": ", ".join(log.competing_events)
                })

    @staticmethod
    def export_state_history(state_history: Dict[str, List[Dict[str, Any]]], output_path: str) -> None:
        """
        Exports the reconstructed time-series state history to JSON.
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(state_history, f, indent=2)