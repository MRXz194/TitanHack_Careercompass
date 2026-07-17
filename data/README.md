# data/ — Pipeline & Datasets

Đọc [docs/DATA_PIPELINE.md](../docs/DATA_PIPELINE.md) để hiểu toàn bộ flow trước khi chạy.

```
pipeline/    # 5 bước, chạy theo thứ tự: crawl → normalize → extract_skills → build_market_stats → embed_careers
taxonomy/    # skills_vi.json — từ điển kỹ năng VN (MI-01 mở rộng ~300 skills)
raw/         # output crawl (gitignored — mỗi người tự chạy hoặc nhận file qua group)
processed/   # output các bước xử lý (gitignored)
seed/        # careers_seed.json — Career KB + demo data (ĐƯỢC commit)
```

⚠️ File trong `raw/` và `processed/` không commit (lớn + đổi liên tục). Dataset chốt
chia sẻ trong group chat dạng zip, hoặc M1 up lên GitHub Release của repo.
