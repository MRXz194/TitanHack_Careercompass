// F1-02: Enter gửi / Shift+Enter xuống dòng, chặn rỗng + double-send, disabled khi pending/done.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ChatComposer } from "@/components/chat/ChatComposer";

describe("ChatComposer", () => {
  it("gõ text + Enter → gọi onSend đúng text và clear ô nhập", async () => {
    const onSend = vi.fn();
    render(<ChatComposer disabled={false} onSend={onSend} />);
    const box = screen.getByRole("textbox");
    await userEvent.type(box, "em thích vẽ{Enter}");
    expect(onSend).toHaveBeenCalledExactlyOnceWith("em thích vẽ");
    expect(box).toHaveValue("");
  });

  it("Shift+Enter xuống dòng, KHÔNG gửi", async () => {
    const onSend = vi.fn();
    render(<ChatComposer disabled={false} onSend={onSend} />);
    await userEvent.type(screen.getByRole("textbox"), "dòng 1{Shift>}{Enter}{/Shift}dòng 2");
    expect(onSend).not.toHaveBeenCalled();
    expect(screen.getByRole("textbox")).toHaveValue("dòng 1\ndòng 2");
  });

  it("text rỗng/khoảng trắng → Enter không gửi", async () => {
    const onSend = vi.fn();
    render(<ChatComposer disabled={false} onSend={onSend} />);
    await userEvent.type(screen.getByRole("textbox"), "   {Enter}");
    expect(onSend).not.toHaveBeenCalled();
  });

  it("disabled → không gõ được, nút Gửi disabled", async () => {
    const onSend = vi.fn();
    render(<ChatComposer disabled onSend={onSend} />);
    expect(screen.getByRole("textbox")).toBeDisabled();
    expect(screen.getByRole("button", { name: /gửi/i })).toBeDisabled();
  });

  it("double-click nút Gửi chỉ gửi 1 lần (text đã clear sau lần 1)", async () => {
    const onSend = vi.fn();
    render(<ChatComposer disabled={false} onSend={onSend} />);
    await userEvent.type(screen.getByRole("textbox"), "xin chào");
    await userEvent.dblClick(screen.getByRole("button", { name: /gửi/i }));
    expect(onSend).toHaveBeenCalledTimes(1);
  });

  it("giữ nguyên emoji/tiếng Việt có dấu", async () => {
    const onSend = vi.fn();
    render(<ChatComposer disabled={false} onSend={onSend} />);
    await userEvent.type(screen.getByRole("textbox"), "em thích vẽ 🎨 và điện tử{Enter}");
    expect(onSend).toHaveBeenCalledWith("em thích vẽ 🎨 và điện tử");
  });
});
