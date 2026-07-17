/**
 * PR-09 transparency copy — source for /how-it-works (M4 content, M6 layout).
 * Keep user-facing Vietnamese friendly; no jargon; no hiring guarantees.
 * Main body target: ≤300 words (see wordCountMainBody()).
 */

export const TRANSPARENCY_COPY_VERSION = "transparency-v1";

/** Forbidden overclaim fragments (checked against PAGE/TOOLTIP bodies only). */
export const FORBIDDEN_PHRASES = [
  "ai biết hơn",
  "ai biết tốt nhất",
  "ai knows best",
  "chắc chắn có việc",
  "bảo đảm có việc",
  "đảm bảo có việc",
  "guaranteed job",
  "nghề tốt nhất",
  "phán quyết",
  "xác suất được tuyển",
  "thiếu người",
  "khan hiếm lao động",
] as const;

export type TooltipKey =
  | "demand_proxy"
  | "match_score"
  | "stretch"
  | "region_pref"
  | "readiness_band"
  | "source_note";

export const TOOLTIPS: Record<TooltipKey, { label: string; text: string }> = {
  demand_proxy: {
    label: "Radar nhu cầu kỹ năng",
    text:
      "Xếp theo số tin tuyển trong snapshot — tín hiệu cầu tuyển dụng, không đo trực tiếp cung–cầu lao động.",
  },
  match_score: {
    label: "Độ phù hợp",
    text:
      "Ưu tiên khớp hồ sơ của bạn (sở thích, kỹ năng có bằng chứng), rồi mới tới tín hiệu thị trường.",
  },
  stretch: {
    label: "Có thể bạn chưa nghĩ tới",
    text: "Một hướng ngoài cụm sở thích chính để mở rộng lựa chọn — vẫn chỉ là tham khảo.",
  },
  region_pref: {
    label: "Vùng ưu tiên",
    text:
      "Chỉ đổi thông tin thị trường theo vùng. Không loại nghề vì bạn ở tỉnh hay thành phố.",
  },
  readiness_band: {
    label: "Mức sẵn sàng (Launch)",
    text:
      "Mức chuẩn bị hồ sơ so với kỹ năng vai trò thường yêu cầu. Không phải tỉ lệ chắc chắn được nhận việc.",
  },
  source_note: {
    label: "Nguồn số liệu",
    text: "Mọi số thị trường có ghi chú nguồn/snapshot. Dữ liệu mỏng thì hệ thống nói rõ, không bịa số.",
  },
};

export const PAGE = {
  title: "Cách CareerCompass hoạt động",
  intro:
    "CareerCompass hỗ trợ khám phá hướng học/nghề (Explore) hoặc chuẩn bị việc entry-level (Launch). Đây là tài liệu tham khảo — quyết định cuối cùng là của bạn.",
  sections: [
    {
      id: "data",
      heading: "Dữ liệu thị trường",
      body:
        "Dùng tin tuyển dụng Việt Nam trong snapshot khoảng 90 ngày. Số tin, lương quan sát và xu hướng là tín hiệu cầu tuyển dụng (Radar nhu cầu kỹ năng), không kết luận cung lao động khi chưa có dữ liệu phù hợp.",
    },
    {
      id: "profile",
      heading: "Hồ sơ từ hội thoại",
      body:
        "Hồ sơ hình thành từ câu trả lời của bạn, hiện live và sửa được. Không có trường giới tính. Vùng chỉ là ưu tiên xem số liệu, không phải bộ lọc cứng để loại nghề.",
    },
    {
      id: "scoring",
      heading: "Cách gợi ý được xếp",
      body:
        "Điểm phù hợp ưu tiên khớp hồ sơ, sau đó mới tới tín hiệu thị trường (có trần để ngành “hot” không lấn át khi bạn không hợp). Mỗi nghề có nhiều lộ trình, gồm đường nghề/cao đẳng/chứng chỉ. Có thêm một gợi ý mở rộng lựa chọn.",
    },
    {
      id: "modes",
      heading: "Hai chế độ Explore và Launch",
      body:
        "Explore: hướng nghề và lộ trình học. Launch: kỹ năng đã có bằng chứng hoặc còn thiếu, mức sẵn sàng hồ sơ (không hứa tỉ lệ nhận việc), gợi ý tìm việc và kế hoạch 30 ngày kèm sản phẩm kiểm tra được.",
    },
    {
      id: "limits",
      heading: "Giới hạn và quyền của bạn",
      body:
        "Không chấm CV, không nộp đơn hộ, không hứa việc hay lương cá nhân. Bạn có thể sửa hồ sơ, xóa phiên và bỏ qua gợi ý. Số liệu và xếp hạng được kiểm soát bằng quy tắc; AI chủ yếu hỗ trợ diễn đạt.",
    },
  ],
  footer: "Gợi ý chỉ mang tính tham khảo — quyết định là của bạn.",
} as const;

/** Plain main-body text used for the ≤300 word gate (title excluded). */
export function mainBodyPlainText(): string {
  const parts = [
    PAGE.intro,
    ...PAGE.sections.map((s) => `${s.heading}. ${s.body}`),
    PAGE.footer,
  ];
  return parts.join(" ");
}

/** Approximate Vietnamese word count (whitespace-separated tokens). */
export function wordCountMainBody(): number {
  return mainBodyPlainText()
    .trim()
    .split(/\s+/)
    .filter(Boolean).length;
}
