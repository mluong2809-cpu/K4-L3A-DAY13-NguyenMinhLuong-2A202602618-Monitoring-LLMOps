"""Render the six-panel lab dashboard from data/logs.jsonl.

Run ``python scripts/render_dashboard.py`` and open ``data/dashboard.html``.
The file is intentionally dependency-free so it can be used as local runtime
evidence without a Grafana or Streamlit installation.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean


REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
OUTPUT_PATH = REPO_ROOT / "data" / "dashboard.html"
WINDOW_MINUTES = 60


def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * percent / 100
    lower, upper = int(position), min(int(position) + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def fmt(value: float | int | None, suffix: str = "") -> str:
    return "no data" if value is None else f"{value:,.2f}{suffix}"


def load_recent_records() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=WINDOW_MINUTES)
    records: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
            timestamp = datetime.fromisoformat(record["ts"].replace("Z", "+00:00"))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue
        if timestamp >= cutoff:
            records.append(record)
    return records


def panel(title: str, unit: str, threshold: str, rows: list[tuple[str, str]]) -> str:
    values = "".join(
        f"<div class='metric'><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></div>"
        for label, value in rows
    )
    return (
        "<section class='panel'>"
        f"<h2>{html.escape(title)}</h2><p class='meta'>Unit: {html.escape(unit)} · Threshold: {html.escape(threshold)}</p>"
        f"{values}</section>"
    )


def render(records: list[dict]) -> str:
    responses = [record for record in records if record.get("event") == "response_sent"]
    requests = [record for record in records if record.get("event") == "request_received"]
    failures = [record for record in records if record.get("event") == "request_failed"]
    latencies = [float(record["latency_ms"]) for record in responses if "latency_ms" in record]
    ttfts = [float(record["ttft_ms"]) for record in responses if "ttft_ms" in record]
    costs = [float(record.get("cost_usd", 0)) for record in responses]
    tokens_in = sum(int(record.get("tokens_in", 0)) for record in responses)
    tokens_out = sum(int(record.get("tokens_out", 0)) for record in responses)
    qualities = [float(record["quality_score"]) for record in responses if "quality_score" in record]
    tool_events = [record for record in records if record.get("tool_success") is not None]
    tool_success = sum(record.get("tool_success") is True for record in tool_events)
    retrieval_rate = 100 * tool_success / len(tool_events) if tool_events else None
    error_rate = 100 * len(failures) / len(requests) if requests else None
    error_types: dict[str, int] = {}
    for failure in failures:
        name = str(failure.get("error_type", "unknown"))
        error_types[name] = error_types.get(name, 0) + 1
    breakdown = ", ".join(f"{name}: {count}" for name, count in error_types.items()) or "none"

    panels = [
        panel("1. Latency percentiles and TTFT", "ms", "P95 latency ≤ 3,000 ms", [
            ("P50 latency", fmt(percentile(latencies, 50), " ms")),
            ("P95 latency", fmt(percentile(latencies, 95), " ms")),
            ("P99 latency", fmt(percentile(latencies, 99), " ms")),
            ("TTFT P95", fmt(percentile(ttfts, 95), " ms")),
        ]),
        panel("2. Request traffic", "requests/minute", "≥ 1 request/minute", [
            ("Requests", str(len(requests))),
            ("Rate", fmt(len(requests) / WINDOW_MINUTES, " req/min")),
        ]),
        panel("3. Errors and retrieval success", "percent", "Errors ≤ 2%; retrieval ≥ 90%", [
            ("Error rate", fmt(error_rate, "%")),
            ("Error breakdown", breakdown),
            ("Retrieval success", fmt(retrieval_rate, "%")),
        ]),
        panel("4. Cost", "USD", "Total ≤ $2.50", [
            ("Total cost", fmt(sum(costs), " USD")),
            ("Average/request", fmt(sum(costs) / len(costs) if costs else None, " USD")),
        ]),
        panel("5. Input and output tokens", "tokens", "Total ≤ 50,000", [
            ("Input tokens", f"{tokens_in:,}"),
            ("Output tokens", f"{tokens_out:,}"),
        ]),
        panel("6. Quality proxy", "score (0–1)", "Mean ≥ 0.75", [
            ("Mean quality", fmt(mean(qualities) if qualities else None)),
            ("Responses scored", str(len(qualities))),
        ]),
    ]
    generated = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><title>LLMOps dashboard</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 32px; background:#f6f8fb; color:#172033; }}
h1 {{ margin-bottom: 4px; }} .subtitle,.meta {{ color:#5c677d; }}
.grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; margin-top:24px; }}
.panel {{ background:white; border:1px solid #dce2ec; border-radius:12px; padding:18px; }}
h2 {{ font-size:17px; margin:0; }} .metric {{ display:flex; justify-content:space-between; gap:12px; padding:10px 0; border-top:1px solid #edf0f5; }}
.metric:first-of-type {{ margin-top:12px; }} strong {{ text-align:right; }}
@media(max-width:700px) {{ .grid {{ grid-template-columns:1fr; }} }}
</style></head><body>
<h1>K4-L3A Monitoring &amp; LLMOps dashboard</h1>
<p class='subtitle'>Time range: last 60 minutes · Source: data/logs.jsonl · Generated: {html.escape(generated)}</p>
<div class='grid'>{''.join(panels)}</div>
</body></html>"""


def main() -> None:
    OUTPUT_PATH.write_text(render(load_recent_records()), encoding="utf-8")
    print(f"Dashboard written to {OUTPUT_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
