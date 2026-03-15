import { NextResponse } from "next/server";
import { loadAssignments, loadRollingIndex } from "@/lib/snapshots";
import type { Assignment } from "@/lib/types";

interface RouteParams {
  params: Promise<{ date: string; time: string }>;
}

/** Returns all class assignments for a given snapshot. */
export async function GET(_req: Request, { params }: RouteParams) {
  const { date, time: rawTime } = await params;
  const dirTime = decodeURIComponent(rawTime).replace(/:/g, "");

  const index = await loadRollingIndex();
  const snap = index.snapshots.find(
    (s) => s.date === date && s.time === dirTime
  );
  if (!snap) {
    return NextResponse.json({ error: "Snapshot not found" }, { status: 404 });
  }

  const result: Record<string, Assignment[]> = {};
  for (const slug of Object.keys(snap.classes)) {
    result[slug] = await loadAssignments(date, dirTime, slug);
  }

  return NextResponse.json(result);
}
