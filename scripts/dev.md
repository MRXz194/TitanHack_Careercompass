# DEV RUNBOOK — setup, verify, demo

## 1. Yêu cầu

- Git, Python 3.11, Node.js 20+.
- Clone repo, copy `.env.example` thành `backend/.env`; không commit file `.env`.
- Frontend mock mode chạy được mà không cần API key.

## 2. Chạy local

Terminal 1:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r ..\data\requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Terminal 2:

```powershell
cd frontend
npm install
Copy-Item ..\.env.example .env.local  # chỉ tham khảo; giữ 2 biến NEXT_PUBLIC_*
npm run dev
```

Mở `http://localhost:3000`; API docs tại `http://localhost:8000/docs`.

## 3. Kiểm tra trước PR

```powershell
cd backend
python -m pip install -r requirements.txt -r ..\data\requirements.txt
python -m compileall app scripts tests
python -m pytest -q tests/unit tests/contract
python -m pytest -q tests/integration
python -m scripts.check_routes

cd ..\frontend
npm run typecheck
npm run build
```

Nếu chưa có test cho package đang sửa, chạy endpoint/page liên quan và ghi rõ lệnh + kết quả trong PR.

## 4. Các mode

| Mode | Frontend | Backend | Dùng khi |
|---|---|---|---|
| Mock | `NEXT_PUBLIC_USE_MOCK=1` | không cần | FE phát triển độc lập |
| Live | `NEXT_PUBLIC_USE_MOCK=0` | `DEMO_MODE=off` | integration/E2E |
| Replay | `NEXT_PUBLIC_USE_MOCK=0` | `DEMO_MODE=replay` | demo mất mạng/model lỗi |

## 5. Troubleshoot nhanh

- `python` mở Microsoft Store: cài Python 3.11 và chọn “Add to PATH”, mở terminal mới.
- PowerShell chặn activate: chạy Python bằng `.\.venv\Scripts\python.exe` thay vì đổi policy máy.
- Port bận: `Get-NetTCPConnection -LocalPort 3000,8000`; dừng đúng process của dự án hoặc đổi port và env.
- Sai version Node (`npm install`/`npm run build` lỗi lạ): `node -v` phải ≥20; dùng `nvm`/`nvm-windows` hoặc cài lại Node 20 LTS, không cố chạy Node 18/22 chưa test.
- CORS: `CORS_ORIGINS` phải đúng origin frontend, không có path.
- FE vẫn dùng mock: kiểm tra `frontend/.env.local`, restart `npm run dev` sau khi đổi env.
- Backend crash "field required"/thiếu env: đối chiếu từng biến trong `backend/.env` với `.env.example`; thiếu key nào là báo lỗi đúng key đó, không phải lỗi ngẫu nhiên.
- LLM JSON fail: xem log metadata, test `DEMO_MODE=replay`; không paste API key vào issue.

## 6. Demo checklist 2 phút

1. `/api/health` OK và `postings_count` đúng snapshot.
2. Mở sẵn `/`, `/explore`, `/market`; notification tắt.
3. Chạy persona A một lần; nếu live fail, chuyển replay và restart BE.
4. Có video backup và file `docs/EVALUATION_RESULTS.md`/data report sẵn để mở.
