# components/

Trích components ra khỏi file trang (`app/*/page.tsx`) khi trang vượt ~150 dòng — xem `frontend/CLAUDE.md`.

Cấu trúc dự kiến (tạo folder khi có component đầu tiên, đừng tạo trước rỗng):

- `chat/` — ChatBubble, ChatInput, PhaseIndicator (M5)
- `profile/` — ProfileCard, DimensionBar, SkillChip, ProfileEditModal (M5)
- `results/` — CareerCard, EvidenceTab, PathwayTab, StretchBadge (M6)
- `market/` — SkillGapBar, RegionSwitcher, RisingCareerList (M6)
- `ui/` — Button, Badge, Skeleton — dùng chung 2 bên
