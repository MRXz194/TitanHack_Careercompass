# M5 — Frontend Explore/Launch Chat and Editable Profile

**Mission:** làm người dùng hiểu bước tiếp theo, thấy profile hình thành và sửa được mọi inference quan trọng.

**Owned:** `/explore`, chat/profile components, session/mode UI. **Buddy:** M6; API consumer M4.

## Task cards

### F1-01 — Mode-aware explore shell (H+0→4)
- **Actions:** landing CTA passes `explore|launch`; two-column chat/profile; mobile drawer; semantic headings/focus.
- **Expected:** mode visible/changeable before first answer; after first turn changing mode asks reset confirmation.
- **Tests:** desktop/mobile; keyboard tab; reload; direct URL/default Explore.
- **Fallback:** shared layout/copy with one mode badge; no separate duplicated pages.

### F1-02 — Chat UI on mock (H+4→10)
- **Actions:** bubbles, input, typing, retry, auto-scroll, disabled submit, one message at a time, network states.
- **Expected:** full 7–10 turn mock; no duplicate sends; Vietnamese error fallback.
- **Tests:** enter/shift-enter, double click, long text, empty/emoji, failed promise, mobile keyboard.
- **Fallback:** no animation/streaming; reliability first.

### F1-03 — Live Profile Card (H+8→14)
- **Actions:** dimensions, skills/evidence, constraints; Launch education/job goal/experience cards; changed-field highlight.
- **Expected:** user sees source quote for inferred skill; empty/unknown states honest.
- **Tests:** partial profile, null fields, long Vietnamese, 0/1 dimensions, experience no skills.
- **Fallback:** bars/chips instead of radar; no chart dependency for profile.

### F1-04 — Profile correction/autonomy (H+12→16)
- **Actions:** edit/remove skill/interest/experience; stage/job goal; confirmation and optimistic rollback.
- **Expected:** correction persists and next recommendation changes when relevant.
- **Tests:** mock + live patch; 404/session reset; remove nonexistent; duplicate experience; API failure rollback.
- **Security:** no free-form HTML; explain delete/reset.

### F1-05 — Live chat integration (H+16→20)
- **Actions:** all API through `lib/api.ts`; journey mode opening; loading/retry; phase/progress without false precision.
- **Expected:** 10-turn Explore + Launch valid; profile update stable.
- **Tests:** live/replay/mock; timeout/422/500; refresh; browser console no error.
- **Fallback:** switch env to replay/mock, visible demo label if data is mock.

### F1-06 — Transition to results (H+20→24)
- **Actions:** only enable CTA when `done`; final profile review; call recommendation once; preserve session/mode.
- **Expected:** chat→results no data in query string; loading and retry; no accidental duplicate generation.
- **Tests:** premature CTA, back/forward, direct results without session, retry.

### F1-07 — UX/copy polish (H+30→38)
- **Actions:** prioritize user-test blockers; clear mode-specific examples; skeleton/empty; reduced motion.
- **Expected:** outsider always knows what to answer/do; no judgmental/guaranteed language.
- **Tests:** copy audit, 200% zoom, reduced motion, slow network, screen widths 360/768/1440.
- **Fallback:** cut animation first.

### F1-08 — Cross-browser/responsive (H+38→42)
- **Actions:** Chrome + one secondary browser/mobile viewport; focus/scroll/modal/drawer.
- **Expected:** no horizontal overflow; CTA/input visible; result handoff intact.
- **Verify:** screenshot checklist and issue links.

### F1-09 — Usability/privacy test support (H+31→38)
- **Actions:** observe ≥5 students, no coaching; time/tasks/errors; Launch and Explore; session delete/privacy copy.
- **Expected:** anonymized report; Sev priority; one fix before freeze.
- **Tests:** delete clears local+server; no transcript in analytics/log/screenshot.

## Component architecture

```text
app/explore/page.tsx
components/chat/ModeSelector.tsx
components/chat/ChatThread.tsx
components/chat/ChatComposer.tsx
components/profile/ProfilePanel.tsx
components/profile/ExperienceList.tsx
components/profile/ProfileEditor.tsx
lib/api.ts + lib/mock/*
```

Page orchestrates; components render; API client owns network; no fetch in component.
