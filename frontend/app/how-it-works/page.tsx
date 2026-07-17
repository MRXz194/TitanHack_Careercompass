// Trang "Cách hệ thống hoạt động" — copy PR-09 (M4); layout tối giản để M6 polish (F2-06).
import Link from "next/link";

import { PAGE, TOOLTIPS, TRANSPARENCY_COPY_VERSION } from "@/lib/copy/transparency";

export default function HowItWorksPage() {
  return (
    <main className="mx-auto max-w-2xl space-y-6 p-6">
      <div className="space-y-2">
        <p className="text-xs text-[var(--cc-muted)]">
          <Link href="/" className="underline">
            Trang chủ
          </Link>
          {" · "}
          bản copy {TRANSPARENCY_COPY_VERSION}
        </p>
        <h1 className="text-2xl font-bold text-[var(--cc-fg)]">{PAGE.title}</h1>
        <p className="text-sm leading-relaxed text-[var(--cc-fg)]">{PAGE.intro}</p>
      </div>

      <ol className="list-decimal space-y-4 pl-5 text-sm leading-relaxed text-[var(--cc-fg)]">
        {PAGE.sections.map((section) => (
          <li key={section.id} className="pl-1">
            <h2 className="font-semibold">{section.heading}</h2>
            <p className="mt-1 text-[var(--cc-muted)]">{section.body}</p>
          </li>
        ))}
      </ol>

      <section className="space-y-2 rounded-lg border border-[var(--cc-border)] bg-[var(--cc-surface)] p-4">
        <h2 className="text-sm font-semibold text-[var(--cc-fg)]">Thuật ngữ nhanh</h2>
        <dl className="space-y-3 text-sm">
          {(Object.keys(TOOLTIPS) as (keyof typeof TOOLTIPS)[]).map((key) => (
            <div key={key}>
              <dt className="font-medium text-[var(--cc-fg)]">{TOOLTIPS[key].label}</dt>
              <dd className="text-[var(--cc-muted)]">{TOOLTIPS[key].text}</dd>
            </div>
          ))}
        </dl>
      </section>

      <p className="border-t border-[var(--cc-border)] pt-4 text-sm font-medium text-[var(--cc-fg)]">
        {PAGE.footer}
      </p>
    </main>
  );
}
