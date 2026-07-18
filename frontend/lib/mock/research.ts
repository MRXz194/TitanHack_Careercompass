import type { CareerResearchResponse, Region, ResearchIntent } from "@/types";
import { mockRecommendations } from "./recommendations";

export async function mockCareerResearch(
  careerIds: string[],
  intent: ResearchIntent,
  region: Region,
): Promise<CareerResearchResponse> {
  const data = await mockRecommendations("explore");
  const options = [...data.recommendations, data.stretch];
  return {
    status: "replay",
    generated_at: new Date().toISOString(),
    intent,
    region,
    disclaimer: "Nguồn web giúp em tự kiểm chứng thêm và không làm thay đổi thứ hạng gợi ý.",
    limitation: "Đây là fixture replay để demo không phụ thuộc mạng; liên kết live chỉ bật khi backend qua quality gate.",
    careers: careerIds.slice(0, 2).flatMap((careerId) => {
      const item = options.find((option) => option.career_id === careerId);
      if (!item) return [];
      return [{
        career_id: item.career_id,
        title: item.title,
        local_market: item.market,
        sources: [
          {
            title: `Tìm hiểu yêu cầu tuyển dụng cho ${item.title}`,
            url: "https://www.vietnamworks.com/",
            domain: "vietnamworks.com",
            snippet: "Nguồn tham khảo tin tuyển dụng; hãy kiểm tra ngày đăng và yêu cầu cụ thể của từng vị trí.",
            source_tier: "job_board" as const,
            retrieved_at: new Date().toISOString(),
          },
        ],
      }];
    }),
  };
}
