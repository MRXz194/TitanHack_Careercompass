// /explore — server component đọc ?mode= rồi giao cho ExploreClient (F1-01: default explore).
import { ExploreClient } from "./ExploreClient";

export default async function ExplorePage({
  searchParams,
}: {
  searchParams: Promise<{ mode?: string; new?: string }>;
}) {
  const { mode, new: fresh } = await searchParams;
  return (
    <ExploreClient
      initialMode={mode === "launch" ? "launch" : "explore"}
      freshStart={fresh === "1"}
    />
  );
}
