import json
import os
import time
from typing import Optional


class LatencyReporter:
    def __init__(self, output_dir: str = "latency_reports"):
        self.output_dir = output_dir
        self.camera_fps_samples = []
        self.input_age_samples = []
        os.makedirs(self.output_dir, exist_ok=True)

    def record(self, camera_fps: Optional[float], input_age_ms: Optional[float]):
        if camera_fps is not None:
            self.camera_fps_samples.append(float(camera_fps))
        if input_age_ms is not None:
            self.input_age_samples.append(float(input_age_ms))

    def _percentile(self, values, percentile: float) -> float:
        if not values:
            return 0.0
        values = sorted(values)
        if len(values) == 1:
            return values[0]
        idx = int(round((percentile / 100.0) * (len(values) - 1)))
        return values[max(0, min(len(values) - 1, idx))]

    def _stats(self, values):
        if not values:
            return None
        values = list(values)
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "p95": self._percentile(values, 95.0),
        }

    def _latest_report_path(self) -> Optional[str]:
        if not os.path.isdir(self.output_dir):
            return None
        candidates = [
            os.path.join(self.output_dir, name)
            for name in os.listdir(self.output_dir)
            if name.endswith(".json")
        ]
        if not candidates:
            return None
        candidates.sort(key=os.path.getmtime)
        return candidates[-1]

    def _load_previous_report(self) -> Optional[dict]:
        path = self._latest_report_path()
        if path is None:
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None

    def _format_value(self, value: Optional[float], unit: str = "") -> str:
        if value is None:
            return "n/a"
        return f"{value:0.1f}{unit}"

    def _format_change(self, prev: Optional[float], curr: Optional[float], lower_is_better: bool) -> str:
        if prev is None or curr is None or prev == 0:
            return "n/a"
        if lower_is_better:
            pct = (prev - curr) / prev * 100.0
        else:
            pct = (curr - prev) / prev * 100.0
        sign = "+" if pct >= 0 else ""
        return f"{sign}{pct:0.1f}%"

    def finalize(self) -> Optional[str]:
        if not self.camera_fps_samples and not self.input_age_samples:
            return None

        now = time.strftime("%Y%m%d_%H%M%S")
        current = {
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "camera_fps": self._stats(self.camera_fps_samples),
            "input_age_ms": self._stats(self.input_age_samples),
        }
        previous = self._load_previous_report()

        json_path = os.path.join(self.output_dir, f"latency_{now}.json")
        with open(json_path, "w", encoding="utf-8") as handle:
            json.dump(current, handle, indent=2)

        prev_input = previous.get("input_age_ms") if previous else None
        prev_fps = previous.get("camera_fps") if previous else None
        curr_input = current.get("input_age_ms")
        curr_fps = current.get("camera_fps")

        md_path = os.path.join(self.output_dir, f"latency_{now}.md")
        with open(md_path, "w", encoding="utf-8") as handle:
            handle.write("# Latency Report\n\n")
            handle.write(f"Generated at: {current['generated_at']}\n\n")
            handle.write("| Metric | Previous | Current | Change |\n")
            handle.write("| --- | --- | --- | --- |\n")

            prev_mean = prev_input["mean"] if prev_input else None
            curr_mean = curr_input["mean"] if curr_input else None
            handle.write(
                "| Input age mean (ms) | "
                + self._format_value(prev_mean)
                + " | "
                + self._format_value(curr_mean)
                + " | "
                + self._format_change(prev_mean, curr_mean, lower_is_better=True)
                + " |\n"
            )

            prev_p95 = prev_input["p95"] if prev_input else None
            curr_p95 = curr_input["p95"] if curr_input else None
            handle.write(
                "| Input age p95 (ms) | "
                + self._format_value(prev_p95)
                + " | "
                + self._format_value(curr_p95)
                + " | "
                + self._format_change(prev_p95, curr_p95, lower_is_better=True)
                + " |\n"
            )

            prev_fps_mean = prev_fps["mean"] if prev_fps else None
            curr_fps_mean = curr_fps["mean"] if curr_fps else None
            handle.write(
                "| Camera FPS mean | "
                + self._format_value(prev_fps_mean)
                + " | "
                + self._format_value(curr_fps_mean)
                + " | "
                + self._format_change(prev_fps_mean, curr_fps_mean, lower_is_better=False)
                + " |\n"
            )

        return md_path
