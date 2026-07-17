// /explore — server component đọc ?mode= rồi giao cho ExploreClient (F1-01: default explore).
import { ExploreClient } from "./ExploreClient";

export default async function ExplorePage({
  searchParams,
}: {
  searchParams: Promise<{ mode?: string }>;
}) {
  const { mode } = await searchParams;
  return <ExploreClient initialMode={mode === "launch" ? "launch" : "explore"} />;
}
