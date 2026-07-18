import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { getMockProfile, mockChat, resetMockChat } from "@/lib/mock/chat";
import { mockRecommendations } from "@/lib/mock/recommendations";

async function finish<T>(promise: Promise<T>, milliseconds: number): Promise<T> {
  await vi.advanceTimersByTimeAsync(milliseconds);
  return promise;
}

describe("mock fallback — persona integrity", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    localStorage.clear();
    resetMockChat("explore");
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("hai persona trái ngược không nhận cùng thứ tự gợi ý", async () => {
    await finish(mockChat("Em hay sua quat va sua do dien trong nha", "explore"), 600);
    await finish(mockChat("Em tu lap rap may moc va han day", "explore"), 600);
    const technicalProfile = getMockProfile();
    const technical = await finish(mockRecommendations("explore"), 900);

    resetMockChat("explore");
    await finish(mockChat("Em thich ve tranh va thiet ke poster bang Figma", "explore"), 600);
    await finish(mockChat("Em quay video va dung phim cho cau lac bo", "explore"), 600);
    const creativeProfile = getMockProfile();
    const creative = await finish(mockRecommendations("explore"), 900);

    expect(technicalProfile.dimensions.ky_thuat).toBeGreaterThan(technicalProfile.dimensions.sang_tao);
    expect(creativeProfile.dimensions.sang_tao).toBeGreaterThan(creativeProfile.dimensions.ky_thuat);
    expect(technical.recommendations[0].career_id).toBe("ky-thuat-vien-dien-lanh");
    expect(creative.recommendations[0].career_id).toBe("thiet-ke-do-hoa");
    expect(technical.recommendations.map((item) => item.career_id))
      .not.toEqual(creative.recommendations.map((item) => item.career_id));
  });

  it("phủ định kinh nghiệm không tạo project/Python giả", async () => {
    resetMockChat("launch");
    await finish(mockChat("Em chua co project, chua tung thuc tap va chua biet Python", "launch"), 600);
    await finish(mockChat("Em thich phan tich du lieu va moi hoc Excel co ban", "launch"), 600);
    const profile = getMockProfile();
    expect(profile.experiences).toEqual([]);
    expect(profile.skills.some((skill) => skill.name === "Python")).toBe(false);
    expect(profile.constraints.notes).toMatch(/chưa có project/i);

    const results = await finish(mockRecommendations("launch"), 900);
    for (const item of [...results.recommendations, results.stretch]) {
      expect(item.job_readiness?.matched_skills.some((match) => match.skill === "Python")).toBe(false);
      for (const match of item.job_readiness?.matched_skills ?? []) {
        expect(match.evidence).toContain("moi hoc Excel");
      }
      expect(JSON.stringify(item.job_readiness)).not.toContain("Dashboard bán hàng");
      expect(JSON.stringify(item.job_readiness)).not.toContain("Project Dashboard");
    }
  });

  it("dùng điện thoại/xem video không tự biến thành năng lực kỹ thuật hoặc sáng tạo", async () => {
    await finish(mockChat("Em dùng điện thoại để xem video và chưa rõ mình thích gì", "explore"), 600);
    const profile = getMockProfile();
    expect(Math.max(...Object.values(profile.dimensions))).toBe(0);
    expect(profile.interests).toEqual([]);
  });

  it("không gắn nhãn cá nhân hóa cho hồ sơ hoàn toàn trống", async () => {
    const assertion = expect(mockRecommendations("explore")).rejects.toThrow(/chưa có tín hiệu/i);
    await vi.advanceTimersByTimeAsync(900);
    await assertion;
  });

  it("không lưu email, số điện thoại, secret hoặc nhãn giới trong mock profile", async () => {
    await finish(mockChat(
      "Tên em là Nguyễn Văn An, em là nữ, GPA 3.8/4, địa chỉ: 123 Đường ABC; email student@example.com, số 0912 345 678, key sk-abcdefgh123; em thích thiết kế poster",
      "explore",
    ), 600);
    const persisted = JSON.stringify(getMockProfile());
    expect(persisted).not.toContain("student@example.com");
    expect(persisted).not.toContain("0912 345 678");
    expect(persisted).not.toContain("sk-abcdefgh123");
    expect(persisted).not.toContain("Nguyễn Văn An");
    expect(persisted).not.toContain("3.8");
    expect(persisted).not.toContain("123 Đường ABC");
    expect(persisted.toLocaleLowerCase("vi")).not.toContain("nữ");
    expect(getMockProfile().interests).toEqual(["em thích thiết kế poster"]);
    expect(persisted).toContain("thiết kế poster");
  });

  it("ẩn cả nhãn giới viết không dấu nhưng giữ tín hiệu nghề nghiệp", async () => {
    await finish(mockChat("Em la nu va em thich ve tranh, thiet ke poster", "explore"), 600);
    const persisted = JSON.stringify(getMockProfile()).toLowerCase();
    expect(persisted).not.toContain("em la nu");
    expect(getMockProfile().dimensions.sang_tao).toBeGreaterThan(0);
  });

  it("reload/re-open giữ đúng turn và không ghép hồ sơ cũ với opening mới", async () => {
    const first = await finish(mockChat("Em thích phân tích dữ liệu bằng Excel", "explore"), 600);
    const before = getMockProfile();
    const reopened = await finish(mockChat(null, "explore"), 600);

    expect(reopened.turn).toBe(first.turn);
    expect(reopened.phase).toBe(first.phase);
    expect(reopened.profile).toEqual(before);
    expect(reopened.reply).toMatch(/mở lại hồ sơ demo/i);
  });

  it("turn chỉ có nhãn giới không làm tăng tiến độ profiling", async () => {
    const opened = await finish(mockChat(null, "explore"), 600);
    const privacyOnly = await finish(mockChat("Em là nữ", "explore"), 600);

    expect(privacyOnly.turn).toBe(opened.turn);
    expect(privacyOnly.profile).toEqual(opened.profile);
    expect(privacyOnly.reply).toMatch(/không dùng thông tin nhận dạng/i);
  });
});
