import { redirect } from "next/navigation";
import { loadRollingIndex } from "@/lib/snapshots";
import { formatTime } from "@/lib/format";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ date: string }>;
  searchParams: Promise<{ [key: string]: string | undefined }>;
}

export default async function DayPage({ params, searchParams }: PageProps) {
  const { date } = await params;
  const search = await searchParams;
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
  // Preserve query params (e.g., ?class=) through the redirect
  const queryString = new URLSearchParams(
    Object.fromEntries(Object.entries(search).filter(([, v]) => v !== undefined) as [string, string][])
  ).toString();
  const qs = queryString ? `?${queryString}` : "";
  redirect(`/day/${date}/${formatTime(latest.time)}${qs}`);
}
