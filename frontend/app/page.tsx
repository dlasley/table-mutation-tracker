import CalendarView from "@/components/CalendarView";
import GradeBanner from "@/components/GradeBanner";
import LatestSnapshotLabel from "@/components/LatestSnapshotLabel";
import { loadRollingIndex } from "@/lib/snapshots";

export const dynamic = "force-dynamic";

export default async function Home() {
  const index = await loadRollingIndex();

  // Determine initial month from latest snapshot
  const latestSnap = index.snapshots[index.snapshots.length - 1];
  const now = latestSnap
    ? new Date(latestSnap.date + "T00:00:00")
    : new Date();

  return (
    <div className="space-y-6">
      {latestSnap && (
        <>
          <LatestSnapshotLabel date={latestSnap.date} time={latestSnap.time} />
          {latestSnap.gpa != null && (
            <p className="text-sm text-gray-500 text-center">GPA {latestSnap.gpa.toFixed(2)}</p>
          )}
          <GradeBanner classes={latestSnap.classes} />
        </>
      )}

      <CalendarView
        snapshots={index.snapshots}
        initialYear={now.getFullYear()}
        initialMonth={now.getMonth()}
      />
    </div>
  );
}
