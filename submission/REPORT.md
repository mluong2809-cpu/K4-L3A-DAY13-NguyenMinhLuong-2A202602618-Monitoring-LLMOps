# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Nguyễn Minh Lương
- **MSSV:** 2A202602618
- **Lớp:** K4-L3A
- **Repository URL:** https://github.com/mluong2809-cpu/K4-L3A-DAY13-NguyenMinhLuong-2A202602618-Monitoring-LLMOps
- **Commit SHA cuối:** Cập nhật sau khi tạo commit nộp bài cuối cùng.
- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602618`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | [01-pytest.txt](evidence/01-pytest.txt) |
| Log validator | [02-log-validator.txt](evidence/02-log-validator.txt) |
| Dashboard validator | [03-dashboard-validator.txt](evidence/03-dashboard-validator.txt) |
| Structured log | [04-structured-log.txt](evidence/04-structured-log.txt) |
| PII redaction | [05-pii-redaction.txt](evidence/05-pii-redaction.txt) |
| Trace list | [06-trace-list-restarted.png](evidence/06-trace-list-restarted.png) |
| Trace waterfall | [07-trace-waterfall.png](evidence/07-trace-waterfall.png) |
| Trace metadata | [08-trace-metadata.png](evidence/08-trace-metadata.png) |
| Prompt versions/promote | [09-prompt-versions-promote.png](evidence/09-prompt-versions-promote.png) |
| Prompt rollback | [10-prompt-rollback.png](evidence/10-prompt-rollback.png) |
| Dashboard runtime | [11-dashboard-overview-top.png](evidence/11-dashboard-overview-top.png) (panels 1–4) và [11-dashboard-overview-bottom.png](evidence/11-dashboard-overview-bottom.png) (panels 3–6) |
| Incident metric | [12-incident-metric.png](evidence/12-incident-metric.png) |
| Incident log | [13-incident-log.png](evidence/13-incident-log.png) |
| Incident trace | [14-incident-trace.png](evidence/14-incident-trace.png) |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 50/100 | 100/100 | Baseline thiếu required fields và enrichment; sau khi lưu log baseline, workload mới có correlation/context/PII scrub đạt toàn bộ tiêu chí. |
| `validate_dashboard.py` | 6/6 | 6/6 | Dashboard contract giữ đúng sáu panel. |
| `pytest` | Không ghi nhận | 24 passed | Kết quả cuối chạy bằng interpreter `.venv`. |
| Số traces hợp lệ | 10 | ≥10 | Traces nằm trong project Langfuse cá nhân. |
| Số PII leak | 0 | 0 | Validator và evidence redaction không có PII thô. |
| Latency P95 / TTFT P95 | 1,259.60 ms / 50 ms | 2,654.00 ms / 50 ms | P95 tăng trong challenge `rag_slow`. |
| Retrieval success rate | 100% | 100% | Retrieval không lỗi trong baseline và challenge; challenge làm tăng duration. |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware nhận `x-request-id` hoặc sinh `req-<8-hex>`, bind vào structlog context, trả lại qua `x-request-id` và đưa ID vào trace metadata.
- **Các metadata được ghi vào structured log:** `user_id_hash`, `session_id`, `feature`, `model`, `env`, latency, TTFT, token/cost và trạng thái retrieval.
- **Cách bảo đảm PII được scrub trước khi ghi:** `scrub_event` chạy trước JSON renderer/file writer; email, số điện thoại Việt Nam, CCCD và số thẻ được thay bằng marker `[REDACTED_*]`.
- **Cách kiểm chứng kết quả:** [structured log](evidence/04-structured-log.txt), [PII redaction](evidence/05-pii-redaction.txt) và [log validator 100/100](evidence/02-log-validator.txt).

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** Danh sách trace và metadata thuộc project Langfuse cá nhân, có environment `dev`, user hash và session của workload.
- **Cấu trúc root/retrieval/generation observations:** `lab-agent-run` là root; `retrieval` và `fake-llm-generate` là child observations. Generation ghi model, usage và cost.
- **Cách nối trace với log:** Dùng cùng `correlation_id`, ví dụ incident `req-9e5b0c6e` nối với trace `1dce64a04219275c677b5f34831789ae`.
- **Prompt name:** `day13-chat`.
- **Version/label baseline:** Version 1, label `baseline` và `production`.
- **Version/label candidate:** Version 2, label `candidate`.
- **Trace ID của mỗi version:** v1/`production`: `c4947448e1f4e553614116cd227d59e8`; v2/`candidate`: `c997e1f143c72bad5cbe2bd3bf5a94ad`. Trace v2 hiển thị `prompt_source=langfuse`, `prompt_version=2`, `prompt_label=candidate` và `prompt_name=day13-chat`.
- **Cách promote và rollback `production`:** Đã chuyển label `production` từ v1 sang v2 (ảnh `09-prompt-versions-promote.png`), sau đó chuyển lại từ v2 về v1 (ảnh `10-prompt-rollback.png`). Việc đổi label cho phép deploy hoặc rollback prompt mà không sửa source code.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Sáu panel gồm latency/TTFT, traffic, errors/retrieval success, cost, tokens và quality proxy; dashboard dùng time range 60 phút và threshold từ `config/dashboard.yaml`.
- **SLO và lý do chọn:** SLO là 99.5% request thành công trong không quá 3,000 ms trong 28 ngày; phù hợp với trải nghiệm chat tương tác.
- **Cách tính error budget:** `100 - 99.5 = 0.5%`; với 10,000 request, tối đa 50 request được phép lỗi hoặc vượt 3,000 ms.
- **Ba alert và runbook tương ứng:** `chat_latency_slo_breach`, `chat_error_rate_high`, `retrieval_success_degraded`; xem [config/alert_rules.yaml](../config/alert_rules.yaml) và [docs/alerts.md](../docs/alerts.md). Cấu hình SLO nằm tại [config/slo.yaml](../config/slo.yaml).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3a-monitoring-llmops-v1`
- **Khoảng thời gian điều tra:** 2026-09-29 09:03:05Z–09:03:16Z.
- **Triệu chứng từ metrics:** Dashboard latency panel ghi P95 `2,654 ms` (P99 `2,654.66 ms`), tăng rõ rệt so với workload bình thường; error rate vẫn `0%` và retrieval success vẫn `100%`.
- **Log line và correlation ID liên quan:** `response_sent` lúc `2026-09-29T09:03:13.461652Z`, `correlation_id=req-9e5b0c6e`, `latency_ms=2653`, `ttft_ms=50`, `tool_success=true`.
- **Trace ID và span gây ảnh hưởng:** Trace `1dce64a04219275c677b5f34831789ae` tương ứng request trên. Root agent kéo dài `2.65 s`; retrieval mất `2.50 s`, trong khi `fake-llm-generate` mất `152 ms`.
- **Root cause:** Challenge đã bật điều kiện retrieval chậm (`rag_slow`), làm bước lấy context tăng khoảng 2.5 giây cho mỗi request; vì vậy latency tăng dù không có lỗi retrieval.
- **Fix action:** Tắt incident `rag_slow`, sau đó xác nhận P95 latency trở về baseline bằng workload nhỏ.
- **Preventive measure:** Alert khi P95 latency vượt ngưỡng trong 5 phút; dùng correlation ID để drill down trace, và theo dõi riêng retrieval duration/success để phát hiện regression sớm.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Ghi structured log JSON và bind correlation ID ở middleware để mọi endpoint dùng cùng chuẩn quan sát.
- **Một lỗi/blocker đã gặp:** Baseline log cũ làm validator chỉ đạt 50/100; nguyên nhân là validator đọc toàn bộ file log, gồm dữ liệu trước khi hoàn thiện CP1.
- **Cách tìm nguyên nhân và xử lý:** Lưu log baseline, tạo workload mới sau khi sửa middleware/context/PII scrubber, rồi validator đạt 100/100.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics phát hiện P95 latency tăng; log chọn request `req-9e5b0c6e`; trace cùng ID chỉ ra retrieval mất 2.50 giây.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Prompt label giúp deploy/rollback không sửa code; token/cost phát hiện chi phí bất thường; SLO/alert biến metric thành hành động vận hành.
- **Điều quan trọng nhất đã học:** Một request cần được nối xuyên suốt từ dashboard đến log và trace để kết luận root cause dựa trên bằng chứng.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** Không có hạn chế đã biết trong phạm vi prompt versioning; cần bảo đảm toàn bộ evidence và kết quả kiểm tra cuối thuộc đúng commit SHA được nộp.

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
