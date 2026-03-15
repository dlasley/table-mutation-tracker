import { useState, useEffect, useMemo } from "react";
import type { SnapshotEntry } from "@/lib/types";
import { toLocalDate } from "@/lib/format";

/**
 * Groups snapshots by browser-local date, handling SSR hydration safely.
 * Before mount, falls back to UTC dates to match server render.
 */
export function useLocalSnapshots(snapshots: SnapshotEntry[]) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const byDate = useMemo(() => {
    const map = new Map<string, SnapshotEntry[]>();
    for (const s of snapshots) {
      const key = mounted ? toLocalDate(s.date, s.time) : s.date;
      const list = map.get(key) || [];
      list.push(s);
      map.set(key, list);
    }
    return map;
  }, [snapshots, mounted]);

  const latestByDate = useMemo(() => {
    const map = new Map<string, SnapshotEntry>();
    for (const [date, snaps] of byDate) {
      let latest = snaps[0];
      for (const s of snaps) {
        if (s.time > latest.time) latest = s;
      }
      map.set(date, latest);
    }
    return map;
  }, [byDate]);

  const latestLocalDate = useMemo(() => {
    const last = snapshots[snapshots.length - 1];
    if (!last) return null;
    return mounted ? toLocalDate(last.date, last.time) : last.date;
  }, [snapshots, mounted]);

  return { mounted, byDate, latestByDate, latestLocalDate };
}
