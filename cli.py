import argparse
import sys
import os
import json
from src.ingestion import EventIngestor
from src.reconciliation import ReconciliationEngine
from src.audit import AuditExporter
from src.visualization import StateVisualizer


def main():
    parser = argparse.ArgumentParser(description="Facility Health Reconciliation Engine CLI")
    parser.add_argument("--file", type=str, default="data/fixtures/sample_events.csv", help="Path to input CSV event file")
    parser.add_argument("--replay", action="store_true", help="Replay events and perform determinism validation")
    parser.add_argument("--output-dir", type=str, default="data/outputs", help="Directory to store audit and plot outputs")

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print("==========================================================")
    print("      FACILITY HEALTH RECONCILIATION ENGINE CLI           ")
    print("==========================================================")
    print(f"[*] Input File: {args.file}")
    print(f"[*] Mode: {'REPLAY & DETERMINISM TEST' if args.replay else 'STANDARD RUN'}")

    ingestor = EventIngestor()
    events, stats = ingestor.parse_csv(args.file)

    print(f"[+] Total CSV Rows Read: {stats['total_rows']}")
    print(f"[+] Valid Normalized Events: {stats['valid_events']}")
    print(f"[!] Skipped / Malformed Rows: {stats['skipped_rows']}")

    engine = ReconciliationEngine(window_hours=1.0)
    state_history, audit_logs = engine.reconcile_events(events)

    audit_json_path = os.path.join(args.output_dir, "audit_trail.json")
    audit_csv_path = os.path.join(args.output_dir, "audit_trail.csv")
    state_json_path = os.path.join(args.output_dir, "reconciled_state.json")
    plot_png_path = os.path.join(args.output_dir, "subsystem_health_timeline.png")

    AuditExporter.export_json(audit_logs, audit_json_path)
    AuditExporter.export_csv(audit_logs, audit_csv_path)
    AuditExporter.export_state_history(state_history, state_json_path)
    StateVisualizer.plot_subsystem_timelines(state_history, plot_png_path)

    print(f"[✓] Exported Audit Log (JSON): {audit_json_path}")
    print(f"[✓] Exported Audit Log (CSV) : {audit_csv_path}")
    print(f"[✓] Exported Reconciled State: {state_json_path}")
    print(f"[✓] Rendered Visualization  : {plot_png_path}")

    if args.replay:
        print("\n[*] Executing Determinism Validation Pass...")
        ingestor_2 = EventIngestor()
        events_2, _ = ingestor_2.parse_csv(args.file)
        engine_2 = ReconciliationEngine(window_hours=1.0)
        state_history_2, audit_logs_2 = engine_2.reconcile_events(events_2)

        with open(audit_json_path, "r") as f1:
            run1 = json.load(f1)
        
        audit_json_path_2 = os.path.join(args.output_dir, "audit_trail_replay.json")
        AuditExporter.export_json(audit_logs_2, audit_json_path_2)
        with open(audit_json_path_2, "r") as f2:
            run2 = json.load(f2)

        assert run1 == run2, "DETERMINISM ERROR: Replay output differs from original output!"
        print("[✓] DETERMINISM VERIFIED: Byte-for-byte identical output on replay.")

    print("==========================================================")


if __name__ == "__main__":
    main()