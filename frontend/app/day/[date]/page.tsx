import { redirect } from "next/navigation";
import { loadRollingIndex } from "@/lib/snapshots";
import { formatTime } from "@/lib/format";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ date: string }>;
}

export default async function DayPage({ params }: PageProps) {
  const { date } = await params;
  const index = await loadRollingIndex();

  // Find all snapshots for this date, redirect to the latest
  const daySnapshots = index.snapshots.filter((s) => s.date === date);
  if (daySnapshots.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        No snapshots found for {date}.
        <br />
        <a href="/" className="text-blue-500 hover:underline mt-2 inline-block">Back to calendar</a>
      </div>
    );
  }

  const latest = daySnapshots[daySnapshots.length - 1];
  redirect(`/day/${date}/${formatTime(latest.time)}`);
}
