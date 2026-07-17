import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

// RTL auto-cleanup chỉ chạy khi vitest globals bật — gọi tường minh để DOM sạch giữa các test.
afterEach(cleanup);

// jsdom không có scrollIntoView — stub để ChatThread auto-scroll không crash trong test.
Element.prototype.scrollIntoView = Element.prototype.scrollIntoView ?? (() => {});
