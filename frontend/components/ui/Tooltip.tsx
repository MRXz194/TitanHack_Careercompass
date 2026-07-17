import React from "react";

interface TooltipProps {
  children: React.ReactNode;
  content: string;
}

export default function Tooltip({ children, content }: TooltipProps) {
  return (
    <span className="relative group inline-block">
      {/* Nút trigger di chuột hoặc focus bàn phím */}
      <span 
        className="cursor-help underline decoration-dotted decoration-[var(--cc-muted)] decoration-1 underline-offset-2 hover:text-[var(--cc-primary)] focus-visible:ring-1 focus-visible:ring-[var(--cc-primary)] focus-visible:outline-none transition-all"
        tabIndex={0}
      >
        {children}
      </span>
      
      {/* Bong bóng Tooltip hiển thị khi hover hoặc focus */}
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2.5 w-60 p-3 bg-[var(--cc-ink)] text-[#faf7f2] text-[10px] rounded-xl opacity-0 pointer-events-none group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-200 z-50 text-left font-sans font-normal leading-relaxed shadow-xl border border-white/5">
        {content}
        {/* Mũi tên chỉ xuống */}
        <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-[var(--cc-ink)]" />
      </span>
    </span>
  );
}
