# frontend/CLAUDE.md — Frontend-specific AI context

Read root `CLAUDE.md` first. Frontend = Next.js 15 App Router + TypeScript strict + Tailwind v4 + Recharts.

## Rules

- ALL API calls go through `lib/api.ts`. Never `fetch()` inside components. Mock mode
  (`NEXT_PUBLIC_USE_MOCK=1`) must keep working at all times — update `lib/mock/*` whenever
  the contract changes.
- Types in `types/index.ts` mirror `docs/API_CONTRACT.md`. Don't invent fields; if a field
  is missing, that's a contract discussion (TEAM_RULES.md §2), not a local type edit.
- Pages: `/` landing · `/explore` chat+profile (M5) · `/results` recommendations (M6) ·
  `/market` skill gap radar (M6) · `/how-it-works` transparency page.
- Components go in `components/<area>/` (chat/, profile/, results/, market/, ui/). Extract
  from page files once they grow past ~150 lines.
- Colors: use the `--cc-*` CSS variables in `app/globals.css` (design tokens). Stretch
  card uses `--cc-accent`. Don't introduce new palette colors.
- All user-facing copy in Vietnamese, friendly tone ("em/bạn/mình"), no jargon. Numbers
  formatted Vietnamese-style ("12–18 triệu", `toLocaleString("vi-VN")`).
- Every chart/stat must show its data source note (`source_note` from API).
- Client components only where interactivity requires it; keep pages server-rendered otherwise.
- No new dependencies without asking the team lead (M1). Recharts is the only chart lib.

## Run

```
npm install
npm run dev            # http://localhost:3000
# .env.local: NEXT_PUBLIC_API_BASE=http://localhost:8000, NEXT_PUBLIC_USE_MOCK=1|0
```
