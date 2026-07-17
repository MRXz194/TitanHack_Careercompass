# PREFLIGHT — gate trước khi bấm giờ 48h

> M1 chỉ tuyên bố `READY` khi toàn bộ P0 checkbox pass. Tài liệu chi tiết không thay cho môi trường chạy được.

## A. Product/scope

- [ ] 6/6 hiểu đề bài và nói lại 4 tiêu chí chấm.
- [ ] Explore là live demo chính; Launch là shared-core P1 + replay safety net.
- [ ] P0/P1/P2 và kill switches được cả team chấp nhận.
- [ ] Out-of-scope job board/CV/auto-apply/hiring prediction được chốt.
- [ ] Persona Minh/An và demo timebox được duyệt.

## B. Team/ownership

- [ ] Gán tên thật/GitHub handle vào M1–M6; buddy pairs xác nhận.
- [ ] Mỗi người mở đúng `docs/workstreams/M*.md`, chọn task đầu và nói expected output/test/handoff.
- [ ] Sleep shifts, sync times và `#blockers` sẵn sàng.
- [ ] Không hai người/agent cùng sở hữu một file ở task đầu.

## C. Repo/environment

- [ ] Python 3.11 + Node 20 trên ít nhất 4 máy; 6/6 chạy FE mock.
- [ ] Backend install + smoke tests pass trên ít nhất 2 máy.
- [ ] CI test PR pass; branch protection/review active.
- [ ] `.env` không tracked; dev/demo env matrix và key owner rõ.
- [ ] Mock/live/replay flags được giải thích và thử.

## D. Contract/fixtures

- [ ] API contract + Pydantic + TS + mocks đồng bộ Explore/Launch.
- [ ] Contract version/label trước H+0; breaking change process rõ.
- [ ] Explore/Launch request/result fixtures parse được.
- [ ] Error envelope, null/low-confidence and no-session states có fixture.

## E. Data/AI cost

- [ ] M2 có ít nhất 1 source candidate + Plan B dataset/license.
- [ ] M1 chốt crawl/API/LLM budget và ngưỡng 70% chuyển fallback.
- [ ] LLM/embedding keys test bằng call tối thiểu, không paste key vào chat/issue.
- [ ] Cache/artifact/replay directories và hash/version rule rõ.
- [ ] M4/M1 cài đúng pinned LangChain/LangGraph từ `requirements.txt`; gateway import smoke pass; chốt spike 90 phút, `/api/chat` only, no `create_agent`/prebuilt/checkpointer/LangSmith service; `AGENT_MODE=deterministic` fallback chạy được.
- [ ] M1 chạy test gates theo `TESTING.md`: compile; unit; contract; integration; route invariant. E2E folder/owner đã chốt, chưa có test thì ghi `NOT_IMPLEMENTED`.

## F. Ethics/security/evaluation

- [ ] No-gender/region-not-filter/readiness-not-probability rules được 6/6 hiểu.
- [ ] Data source/PII/session retention checklist có owner.
- [ ] Gold data/persona templates sẵn, không tune trên test set sau khi đo baseline.
- [ ] Người test dự kiến và consent quote template đã liên hệ.

## Go/no-go record

```md
Status: NOT_READY | READY_WITH_CAVEATS | READY
Time/commit: ...
Unmet item + owner + deadline: ...
Approved P0/P1 cuts: ...
M1 sign-off: ...
```

Repo hiện chỉ là `READY_FOR_TEAM_REVIEW` cho đến khi runtime/CI/source/key items được kiểm chứng trên máy team.
