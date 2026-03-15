import { loadRollingIndex, loadAssignments } from "@/lib/snapshots";
import type { Assignment } from "@/lib/types";
import DayDetail from "../DayDetail";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ date: string; time: string }>;
}

export default async function TimePage({ params }: PageProps) {
  const { date, time: rawTime } = await params;
  // Browser URL-encodes colons to %3A; decode then strip colons for directory lookup
  const time = decodeURIComponent(rawTime);
  const dirTime = time.replace(/:/g, "");

  const index = await loadRollingIndex();
  const snap = index.snapshots.find(
    (s) => s.date === date && s.time === dirTime
  );

  if (!snap) {
    return (
      <div className="text-center py-12 text-gray-500">
        No snapshot found for {date} {time}.
        <br />
        <a href={`/day/${date}`} className="text-blue-500 hover:underline mt-2 inline-block">
          View latest for {date}
        </a>
      </div>
    );
  }

  const classAssignments: Record<string, Assignment[]> = {};
  for (const slug of Object.keys(snap.classes)) {
    classAssignments[slug] = await loadAssignments(snap.date, snap.time, slug);
  }

  // All snapshots before this one, for the comparison picker
  const priorSnapshots = index.snapshots.filter((s) => {
    const key = `${s.date}/${s.time}`;
    const currentKey = `${snap.date}/${snap.time}`;
    return key < currentKey;
  });

  return (
    <DayDetail
      date={date}
      snapshot={snap}
      classAssignments={classAssignments}
      allSnapshots={index.snapshots}
      priorSnapshots={priorSnapshots}
    />
  );
}
