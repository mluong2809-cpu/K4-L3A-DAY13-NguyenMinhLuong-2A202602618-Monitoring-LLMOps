# Alert runbooks

These alerts are symptom-based: they describe user impact or an SLO signal,
not an internal implementation name. All notifications go to `#llmops-alerts`.

## Alert 1

- Name: `chat_latency_slo_breach`
- Severity: warning
- Duration: P95 chat latency is above 3,000 ms for 5 minutes.
- Related SLO: 99.5% of requests complete successfully within 3,000 ms.
- User impact: chat responses feel slow or time out.
- First checks:
  1. Confirm the P95/TTFT rise in the latency dashboard panel and note its time range.
  2. Find a slow `correlation_id` in `data/logs.jsonl`.
  3. Open the Langfuse trace with that ID and compare `retrieval` and `fake-llm-generate` duration.
- Temporary mitigation: disable a known slow incident; if retrieval is slow, use the local/fallback retrieval path and reduce traffic if needed.
- Owner: LLMOps on-call.

## Alert 2

- Name: `chat_error_rate_high`
- Severity: critical
- Duration: failed requests exceed 2% for 5 minutes.
- Related SLO: fast successful requests.
- User impact: users receive failed chat requests instead of answers.
- First checks:
  1. Confirm the error-rate panel and inspect the error-type breakdown.
  2. Filter `request_failed` logs for the incident window and select a `correlation_id`.
  3. Inspect the matching Langfuse trace for the observation marked with an error.
- Temporary mitigation: disable the failing incident, retry with the local prompt fallback, and communicate impact in `#llmops-alerts`.
- Owner: API on-call.

## Alert 3

- Name: `retrieval_success_degraded`
- Severity: warning
- Duration: retrieval `tool_success` rate is below 90% for 10 minutes.
- Related guardrail: retrieval success rate at least 90%.
- User impact: answers may be generic, incomplete, or fail when required context is unavailable.
- First checks:
  1. Confirm retrieval success in the errors/retrieval dashboard panel.
  2. Inspect `request_failed` and `tool_name=retrieval` logs for a correlation ID.
  3. Open the matching trace and inspect the `retrieval` observation status and duration.
- Temporary mitigation: disable the retrieval fault, use a known-good fallback corpus, and re-run a small smoke workload.
- Owner: RAG on-call.
