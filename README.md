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