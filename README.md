# Facility Health Reconciliation Engine

A deterministic, time-aware state reconstruction pipeline for multi-source facility telemetry (**IoT Sensors**, **Manual Inspections**, and **Contractor Updates**). Reconciles asynchronous, out-of-order, delayed, and conflicting inputs into an auditable timeline of subsystem health (`HVAC`, `Electrical`, `Plumbing`).

Grounded in real-world campus operations, this engine solves state reconciliation without relying on a single authoritative data source by applying deterministic business rules, source hierarchy, and temporal windowing.

---

## Technical Stack & Dependencies

- **Language:** Python 3.10+
- **Data Schemas & Validation:** Pydantic
- **Data Processing:** Pandas
- **Visualization:** Matplotlib
- **Testing Suite:** Pytest

---

## System Architecture & Module Structure

facility-health-reconciliation-engine/
├── data/
│   ├── fixtures/                  # Edge case CSV test datasets
│   │   └── sample_events.csv
│   └── outputs/                   # Reconstructed states, JSON/CSV audit logs, plots
│       ├── audit_trail.json
│       ├── audit_trail.csv
│       ├── reconciled_state.json
│       └── subsystem_health_timeline.png
├── src/
│   ├── init.py
│   ├── schemas.py                 # Pydantic event models & source priority hierarchy
│   ├── ingestion.py               # Parsing, schema normalization, and malformed row error handling
│   ├── reconciliation.py          # State engine, 1-hour temporal windowing, conflict resolution
│   ├── audit.py                   # JSON/CSV audit trail export utilities
│   └── visualization.py           # Matplotlib state timeline plotter
├── tests/
│   ├── init.py
│   └── test_engine.py             # Pytest automated test suite covering 5 edge cases
├── cli.py                         # CLI entrypoint supporting standard run & --replay
├── requirements.txt               # Dependencies
├── NOTES.md                       # Architectural design notes & edge case specs
└── README.md                      # Setup and execution guide

## Conflict Resolution & Precedence Rules

When multiple events affect the same subsystem within a **1-hour temporal proximity window**, state is determined using deterministic precedence rules:

1. **Source Priority Hierarchy:**
   $$\text{Contractor (Priority 1)} > \text{Manual Inspection (Priority 2)} > \text{IoT Telemetry (Priority 3)}$$
2. **Deterministic Tie-Breaking:**
   - **Contractor vs. Contractor:** Prefers the update associated with the higher/later `work_order_id`.
   - **Manual vs. Manual:** Prefers the report with higher `severity` rating; falls back to arrival timestamp.
   - **IoT vs. IoT:** Selects the reading representing peak severity/outlier state.

---

## Setup & Installation

1. **Clone Repository & Navigate to Folder:**
   ```bash
   git clone <YOUR_REPOSITORY_URL>
   cd facility-health-reconciliation-engine

1. Install dependencies: 
python -m pip install -r requirements.txt

---

## Execution and CLI usage:

1. Execute Engine on Event Stream:
python cli.py --file data/fixtures/sample_events.csv

2. Execute Replay & Determinism Verification:
python cli.py --replay

3. Run Automated Pytest Suite:
python -m pytest tests\test_engine.py -v

---

Edge Case Coverage Matrix
The included fixture (data/fixtures/sample_events.csv) exercises 5 core interacting scenarios:

Late Contractor Arrival: Contractor update retroactively overrides an earlier manual inspection report.

Duplicate Manual Reports: Simultaneous manual reports for Plumbing are tie-broken by highest severity.

IoT Sensor Fluctuations: Rapid high/low telemetry spikes in a 15-minute window are safely reconciled without state thrashing.

Out-of-Order Contractor Event: Contractor completion takes precedence over subsequent manual reports.

Missing/Ambiguous Metadata: Malformed data rows missing timestamps or subsystems are logged to ingestion_errors.log and skipped.

---

Generated Audit Outputs & Artifacts
All outputs are saved to data/outputs/:

audit_trail.json: Decision trace detailing evaluated inputs, winning event, rule applied, and reasoning.

audit_trail.csv: Tabular audit log.

reconciled_state.json: Time-ordered state history for all subsystems.

subsystem_health_timeline.png: Visual timeline graph showing subsystem health states over time.

---

### Step 2: Final Run & Artifact Check

Run your CLI one final time to generate fresh output files:

```powershell
python cli.py --replay

Then check that your data/outputs/ directory contains:

audit_trail.json

audit_trail.csv

reconciled_state.json

subsystem_health_timeline.png