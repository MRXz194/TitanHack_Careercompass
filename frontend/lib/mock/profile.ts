// Mock profile patch — task F1-04 nối API thật; giữ mock hoạt động độc lập không cần backend.
import type { Profile, ProfilePatch } from "@/types";
import { applyPatchLocal } from "@/lib/profile/apply";
import { getMockProfile, setMockProfile } from "./chat";

export async function mockPatchProfile(patch: ProfilePatch): Promise<{ profile: Profile }> {
  await new Promise((r) => setTimeout(r, 300));
  const current = getMockProfile();
  const next: Profile = applyPatchLocal(current, patch);
  setMockProfile(next);
  return { profile: next };
}
