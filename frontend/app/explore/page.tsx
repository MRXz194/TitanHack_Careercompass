// Màn chat profiling + Profile Card — tasks F1-01..F1-06 (M5).
// Skeleton demo gọi sendChat() qua lib/api.ts (mock mode hoạt động sẵn).
"use client";

import { useEffect, useRef, useState } from "react";
import { sendChat } from "@/lib/api";
import type { ChatResponse, Profile } from "@/types";

const DIM_LABELS: Record<string, string> = {
  ky_thuat: "Thực hành – kỹ thuật",
  phan_tich: "Phân tích – logic",
  sang_tao: "Sáng tạo – nghệ thuật",
  xa_hoi: "Con người – xã hội",
  quan_ly: "Tổ chức – kinh doanh",
};

export default function ExplorePage() {
  const [messages, setMessages] = useState<{ role: "ai" | "user"; text: string }[]>([]);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleResponse = (res: ChatResponse) => {
    setMessages((m) => [...m, { role: "ai", text: res.reply }]);
    setProfile(res.profile);
    setDone(res.done);
  };

  useEffect(() => {
    setLoading(true);
    sendChat(null).then(handleResponse).finally(() => setLoading(false));
  }, []);

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: "smooth" }), [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);
    try {
      handleResponse(await sendChat(text));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto grid min-h-screen max-w-6xl gap-6 p-6 md:grid-cols-[1fr_320px]">
      {/* Chat column */}
      <section className="flex flex-col rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`max-w-[80%] rounded-2xl px-4 py-2 ${
                m.role === "ai" ? "bg-[var(--cc-primary-soft)]" : "ml-auto bg-slate-100"
              }`}
            >
              {m.text}
            </div>
          ))}
          {loading && <div className="text-sm text-[var(--cc-muted)]">Đang suy nghĩ…</div>}
          <div ref={bottomRef} />
        </div>
        <div className="flex gap-2 border-t border-slate-200 p-3">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            disabled={loading || done}
            placeholder="Nhắn gì đó cho mình nhé…"
            className="flex-1 rounded-xl border border-slate-300 px-4 py-2 outline-none focus:border-[var(--cc-primary)]"
          />
          <button
            onClick={send}
            disabled={loading || done}
            className="rounded-xl bg-[var(--cc-primary)] px-5 py-2 font-medium text-white disabled:opacity-50"
          >
            Gửi
          </button>
        </div>
        {done && (
          <a
            href="/results"
            className="m-3 rounded-xl bg-[var(--cc-success)] px-4 py-3 text-center font-semibold text-white"
          >
            🎯 Xem hướng đi của em
          </a>
        )}
      </section>

      {/* Profile Card — F1-03 nâng cấp thành radar + animation + editing */}
      <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <h2 className="mb-3 font-semibold">Hồ sơ của em (đang hình thành)</h2>
        {profile ? (
          <div className="space-y-3">
            {Object.entries(profile.dimensions).map(([k, v]) => (
              <div key={k}>
                <div className="flex justify-between text-sm">
                  <span>{DIM_LABELS[k] ?? k}</span>
                  <span className="text-[var(--cc-muted)]">{Math.round(v * 100)}%</span>
                </div>
                <div className="h-2 rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-[var(--cc-primary)] transition-all duration-700"
                    style={{ width: `${v * 100}%` }}
                  />
                </div>
              </div>
            ))}
            {profile.interests.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-2">
                {profile.interests.map((it) => (
                  <span key={it} className="rounded-full bg-[var(--cc-primary-soft)] px-3 py-1 text-xs">
                    {it}
                  </span>
                ))}
              </div>
            )}
            <p className="pt-2 text-xs text-[var(--cc-muted)]">
              Em có thể sửa hồ sơ này bất cứ lúc nào — nó là của em.
            </p>
          </div>
        ) : (
          <p className="text-sm text-[var(--cc-muted)]">Trò chuyện để hồ sơ hiện dần ở đây…</p>
        )}
      </aside>
    </main>
  );
}
