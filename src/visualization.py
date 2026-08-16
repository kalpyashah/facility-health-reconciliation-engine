import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from typing import Dict, List, Any


class StateVisualizer:
    STATE_COLORS = {
        "Normal": "#2ecc71",       # Green
        "Warning": "#f1c40f",      # Yellow
        "Critical": "#e74c3c",     # Red
        "In-Maintenance": "#3498db" # Blue
    }

    @classmethod
    def plot_subsystem_timelines(cls, state_history: Dict[str, List[Dict[str, Any]]], output_png_path: str) -> None:
        """
        Generates a timeline plot displaying subsystem health state changes over time using Matplotlib.
        """
        if not state_history:
            return

        fig, ax = plt.subplots(figsize=(12, 6))

        subsystems = list(state_history.keys())
        y_ticks = list(range(len(subsystems)))
        subsystem_y_map = {sub: i for i, sub in enumerate(subsystems)}

        for sub, entries in state_history.items():
            y_pos = subsystem_y_map[sub]
            timestamps = [datetime.fromisoformat(e["timestamp"]) for e in entries]
            states = [e["state"] for e in entries]
            sources = [e["controlling_source"] for e in entries]

            for i in range(len(timestamps)):
                t = timestamps[i]
                state = states[i]
                source = sources[i]
                color = cls.STATE_COLORS.get(state, "#95a5a6")

                # Plot marker point for state event
                ax.scatter(t, y_pos, color=color, s=150, zorder=3, edgecolors="black", linewidth=1.5)
                ax.annotate(
                    f"{state} ({source})",
                    (t, y_pos),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    fontsize=8,
                    fontweight="bold"
                )

            if len(timestamps) > 1:
                ax.plot(timestamps, [y_pos] * len(timestamps), color="#bdc3c7", linestyle="--", linewidth=1.5, zorder=2)

        ax.set_yticks(y_ticks)
        ax.set_yticklabels(subsystems, fontsize=12, fontweight="bold")
        ax.set_title("Facility Health Reconciliation Engine — Subsystem State Timeline", fontsize=14, fontweight="bold", pad=20)
        ax.set_xlabel("Event Timestamp (UTC)", fontsize=11, fontweight="bold")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))

        plt.xticks(rotation=30)
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.tight_layout()

        plt.savefig(output_png_path, dpi=300)
        plt.close()