# M6 — Frontend Results, Market Radar, Landing, Pitch Visuals

**Mission:** biến core evidence thành UI judge hiểu trong vài giây, đồng thời không che confidence/limitations.

**Owned:** `/results`, `/market`, `/how-it-works`, landing/results/market components. **Buddy:** M5.

## Task cards

### F2-01 — Results shell on contract mock (H+0→6)
- **Actions:** ranked cards, score label “mức tương thích tham khảo”, market badges, source state; mode-aware heading.
- **Expected:** render top 5 + stretch; direct/no-session state; mock data visibly labeled.
- **Tests:** null salary/trend, low confidence, long title, fewer results, loading/error.
- **Fallback:** 3 cards + stretch is P0; virtualization/complex grid unnecessary.

### F2-02 — Explainability/pathway/readiness details (H+6→14)
- **Actions:** tabs/sections Why, Market, Routes; Launch adds readiness/matched/missing/actions/search queries.
- **Expected:** evidence quote visually distinct; non-university route prominent but not forced as “best”.
- **Tests:** Explore job_readiness null; Launch full/partial; missing evidence; action deliverable; keyboard accordion.
- **Fallback:** stacked sections, no tab state complexity.

### F2-03 — Stretch/opportunity expansion (H+12→16)
- **Actions:** distinct stretch card; explain why adjacent; disclaimer/autonomy; compare not rank as verdict.
- **Expected:** judge sees opportunity-expanding design in 3 seconds.
- **Tests:** stretch true, not duplicate top5, counterfactual present, mobile copy.

### F2-04 — Hiring-demand radar (H+14→22, live H+32)
- **Actions:** region switch, demand bars/trend/confidence, rising roles, source/date/sample copy.
- **Expected:** no “shortage” claim; low-confidence hides trend headline; source always visible.
- **Tests:** all regions, empty, source error, tiny sample, very high counts, mock/live parity.
- **Fallback:** accessible bar/list; Recharts polish is P2.

### F2-05 — Live integration (H+28→34)
- **Actions:** swap market/recommend endpoints via client; preserve mocks; session/mode; friendly errors.
- **Expected:** Explore + Launch E2E; schema changes fail in CI, not silently.
- **Tests:** live/replay/mock; 404/422/500; API slow; contract fixtures; browser console.
- **Fallback:** replay with same UI; seed label cannot masquerade as real.

### F2-06 — Landing/transparency (H+22→28, copy H+36)
- **Actions:** problem; two journeys; 3 steps; data/AI limits; CTA; how-it-works final copy.
- **Expected:** 15-second understanding: who, problem, outcome, not a verdict.
- **Tests:** CTA modes; mobile; copy comprehension; no unsupported statistics.

### F2-07 — Visual/accessibility polish (H+30→38)
- **Actions:** tokens, number format vi-VN, tooltip, focus, contrast, reduced motion, screenshot states.
- **Expected:** consistent UI and readable evidence; polish never hides source/caveat.
- **Tests:** 200% zoom, keyboard, color-independent trend, null/low-confidence, print screenshot.
- **Fallback:** cut animation/mini charts before content.

### F2-08 — Pitch assets (H+38→44)
- **Actions:** screenshots from actual build, architecture/business workflow diagram, Explore/Launch side-by-side, counselor future mock clearly labeled.
- **Expected:** ≤10-slide deck inputs; no lorem/seed presented as actual result.
- **Verify:** commit/data snapshot/model labels; M1 claim audit.

### F2-09 — Result provenance panel (H+28→34)
- **Actions:** thêm panel “Dựa trên gì?” lấy từ contract response: evidence học sinh, snapshot/source/date/confidence, scoring factors và alternative/stretch; render fallback label.
- **Expected:** judge trace được lý do mà không nhìn private reasoning hoặc agent trace; market claim luôn đi cùng provenance/limitation.
- **Tests:** source/date missing, low confidence, null salary, replay/mock/live parity, keyboard/mobile; không render raw tool args/CoT.
- **Fallback:** static structured sections từ API fields, không chờ trace UI phức tạp.

## Component architecture

```text
app/results/page.tsx
components/results/RecommendationCard.tsx
components/results/EvidencePanel.tsx
components/results/RoutePanel.tsx
components/results/JobReadinessPanel.tsx
components/results/StretchCard.tsx
app/market/page.tsx
components/market/DemandRadar.tsx
components/market/ConfidenceNote.tsx
```

All formatting in small pure helpers; chart data transforms tested independently; no fetch in components.
