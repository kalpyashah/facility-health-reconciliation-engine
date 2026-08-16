import pandas as pd
import json
import logging
from typing import List, Tuple, Dict, Any
from datetime import datetime
from src.schemas import RawEvent, NormalizedEvent, EventSource, Subsystem, Severity

logging.basicConfig(
    filename="ingestion_errors.log",
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class EventIngestor:
    def __init__(self):
        self.processed_ids = set()

    def parse_csv(self, file_path: str) -> Tuple[List[NormalizedEvent], Dict[str, Any]]:
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            logging.error(f"Failed to read CSV file {file_path}: {str(e)}")
            return [], {"total_rows": 0, "valid_events": 0, "skipped_rows": 0, "errors": [str(e)]}

        valid_events: List[NormalizedEvent] = []
        skipped_count = 0
        errors = []

        for index, row in df.iterrows():
            row_dict = row.to_dict()
            
            # Clean NaN / null values
            cleaned_row = {k: v for k, v in row_dict.items() if pd.notna(v)}

            # Skip duplicate event_ids if present
            event_id = cleaned_row.get("event_id") or f"EVT-{index + 1000}"
            cleaned_row["event_id"] = str(event_id)

            if cleaned_row["event_id"] in self.processed_ids:
                logging.warning(f"Row {index}: Skipping duplicate event_id '{cleaned_row['event_id']}'")
                skipped_count += 1
                continue

            try:
                # Handle timestamp parsing
                if "timestamp" in cleaned_row:
                    cleaned_row["timestamp"] = pd.to_datetime(cleaned_row["timestamp"]).to_pydatetime()

                # Event type normalization
                if "event_type" not in cleaned_row and "source" in cleaned_row:
                    cleaned_row["event_type"] = cleaned_row["source"]

                raw_event = RawEvent(**cleaned_row)

                # Validate severity
                sev_val = raw_event.severity.capitalize() if raw_event.severity else "Low"
                if sev_val not in [s.value for s in Severity]:
                    sev_val = Severity.LOW.value

                normalized = NormalizedEvent(
                    event_id=raw_event.event_id,
                    source=EventSource(raw_event.source),
                    timestamp=raw_event.timestamp,
                    subsystem=Subsystem(raw_event.subsystem),
                    status=raw_event.status,
                    severity=Severity(sev_val),
                    user_id=raw_event.user_id,
                    work_order_id=raw_event.work_order_id,
                    device_id=raw_event.device_id,
                    value=float(raw_event.value) if raw_event.value is not None else None
                )

                valid_events.append(normalized)
                self.processed_ids.add(normalized.event_id)

            except Exception as err:
                skipped_count += 1
                err_msg = f"Row {index} skipped: {str(err)}"
                logging.warning(err_msg)
                errors.append(err_msg)

        stats = {
            "total_rows": len(df),
            "valid_events": len(valid_events),
            "skipped_rows": skipped_count,
            "errors": errors
        }

        return valid_events, stats

    def parse_json_payload(self, json_data: List[Dict[str, Any]]) -> Tuple[List[NormalizedEvent], Dict[str, Any]]:
        valid_events: List[NormalizedEvent] = []
        skipped_count = 0
        errors = []

        for index, item in enumerate(json_data):
            event_id = item.get("event_id") or f"EVT-JSON-{index + 1}"
            item["event_id"] = str(event_id)

            if item["event_id"] in self.processed_ids:
                skipped_count += 1
                continue

            try:
                if isinstance(item.get("timestamp"), str):
                    item["timestamp"] = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))

                raw_event = RawEvent(**item)
                sev_val = raw_event.severity.capitalize() if raw_event.severity else "Low"
                if sev_val not in [s.value for s in Severity]:
                    sev_val = Severity.LOW.value

                normalized = NormalizedEvent(
                    event_id=raw_event.event_id,
                    source=EventSource(raw_event.source),
                    timestamp=raw_event.timestamp,
                    subsystem=Subsystem(raw_event.subsystem),
                    status=raw_event.status,
                    severity=Severity(sev_val),
                    user_id=raw_event.user_id,
                    work_order_id=raw_event.work_order_id,
                    device_id=raw_event.device_id,
                    value=float(raw_event.value) if raw_event.value is not None else None
                )

                valid_events.append(normalized)
                self.processed_ids.add(normalized.event_id)

            except Exception as err:
                skipped_count += 1
                errors.append(f"Item {index} skipped: {str(err)}")

        return valid_events, {
            "total_items": len(json_data),
            "valid_events": len(valid_events),
            "skipped_items": skipped_count,
            "errors": errors
        }