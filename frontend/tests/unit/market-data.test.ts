import { afterEach, describe, expect, it, vi } from "vitest";

import { mockOverview } from "@/lib/mock/market";


afterEach(() => {
  vi.useRealTimers();
});

describe("market demand and trend semantics", () => {
  it("tách demand leaders khỏi tuyên bố tăng trưởng", async () => {
    vi.useFakeTimers();
    const pending = mockOverview("all");
    await vi.advanceTimersByTimeAsync(500);
    const overview = await pending;

    expect(overview.demand_leaders.length).toBeGreaterThan(0);
    expect(overview.demand_leaders.map((item) => item.demand_count)).toEqual(
      [...overview.demand_leaders]
        .sort((a, b) => b.demand_count - a.demand_count)
        .map((item) => item.demand_count),
    );
    expect(overview.demand_leaders[0]).not.toHaveProperty("trend_pct");
    expect(overview.rising_careers[0]).toHaveProperty("trend_pct");
  });
});
