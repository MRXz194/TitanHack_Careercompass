// F1-01: mode đổi tự do trước lượt trả lời đầu; sau đó phải confirm reset ngay trong component.
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ModeSelector } from "@/components/chat/ModeSelector";

describe("ModeSelector", () => {
  it("hiển thị 2 chế độ, chế độ hiện tại được đánh dấu aria-pressed", () => {
    render(<ModeSelector mode="explore" locked={false} onSelect={() => {}} />);
    expect(screen.getByRole("button", { name: /khám phá nghề/i })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: /tìm việc đầu tiên/i })).toHaveAttribute("aria-pressed", "false");
  });

  it("chưa locked → click chế độ khác gọi onSelect ngay", async () => {
    const onSelect = vi.fn();
    render(<ModeSelector mode="explore" locked={false} onSelect={onSelect} />);
    await userEvent.click(screen.getByRole("button", { name: /tìm việc đầu tiên/i }));
    expect(onSelect).toHaveBeenCalledWith("launch");
  });

  it("locked → click chế độ khác KHÔNG gọi onSelect ngay mà hiện confirm", async () => {
    const onSelect = vi.fn();
    render(<ModeSelector mode="explore" locked onSelect={onSelect} />);
    await userEvent.click(screen.getByRole("button", { name: /tìm việc đầu tiên/i }));
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.getByText(/bạn chắc chứ/i)).toBeInTheDocument();
  });

  it("locked → xác nhận trong confirm mới gọi onSelect", async () => {
    const onSelect = vi.fn();
    render(<ModeSelector mode="explore" locked onSelect={onSelect} />);
    await userEvent.click(screen.getByRole("button", { name: /tìm việc đầu tiên/i }));
    await userEvent.click(screen.getByRole("button", { name: /đổi và bắt đầu lại/i }));
    expect(onSelect).toHaveBeenCalledWith("launch");
  });

  it("locked → bấm 'Ở lại' đóng confirm, không đổi mode", async () => {
    const onSelect = vi.fn();
    render(<ModeSelector mode="explore" locked onSelect={onSelect} />);
    await userEvent.click(screen.getByRole("button", { name: /tìm việc đầu tiên/i }));
    await userEvent.click(screen.getByRole("button", { name: /ở lại/i }));
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.queryByText(/bạn chắc chứ/i)).not.toBeInTheDocument();
  });

  it("click lại chính chế độ đang chọn không làm gì", async () => {
    const onSelect = vi.fn();
    render(<ModeSelector mode="explore" locked onSelect={onSelect} />);
    await userEvent.click(screen.getByRole("button", { name: /khám phá nghề/i }));
    expect(onSelect).not.toHaveBeenCalled();
    expect(screen.queryByText(/bạn chắc chứ/i)).not.toBeInTheDocument();
  });
});
