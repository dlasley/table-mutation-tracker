"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import ClassTabs from "@/components/ClassTabs";
import DiffTable from "@/components/DiffTable";
import ChangeLegend from "@/components/ChangeLegend";
import SnapshotCalendarPicker from "@/components/SnapshotCalendarPicker";
import type {
  SnapshotEntry,
  Assignment,
  AssignmentChange,
} from "@/lib/types";
import { diffAssignments } from "@/lib/diff";
import { formatTime } from "@/lib/format";

interface DayDetailProps {
  date: string;
  snapshot: SnapshotEntry;
  classAssignments: Record<string, Assignment[]>;
  allSnapshots: SnapshotEntry[];
  priorSnapshots?: SnapshotEntry[];
}

export default function DayDetail({
  date,
  snapshot,
  classAssignments,
  allSnapshots,
  priorSnapshots = [],
}: DayDetailProps) {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const slugs = useMemo(() => Object.keys(snapshot.classes), [snapshot.classes]);
  const classFromUrl = searchParams.get("class");
  const [activeSlug, setActiveSlug] = useState(
    (classFromUrl && slugs.includes(classFromUrl) ? classFromUrl : slugs[0]) || ""
  );

  // React to ?class= param changes (e.g., agent navigation to same page, different class)
  useEffect(() => {
    if (classFromUrl && slugs.includes(classFromUrl)) {
      setActiveSlug(classFromUrl);
    }
  }, [classFromUrl, slugs]);

  // Comparison state: URL ?compare= param takes priority, then previous_snapshot default
  const compareFromUrl = searchParams.get("compare");
  const [compareRef, setCompareRefState] = useState<string | null>(
    compareFromUrl ?? snapshot.previous_snapshot
  );

  // Sync compareRef to URL
  const setCompareRef = useCallback(
    (ref: string | null) => {
      setCompareRefState(ref);
      const params = new URLSearchParams(searchParams.toString());
      if (ref) {
        params.set("compare", ref);
      } else {
        params.delete("compare");
      }
      const qs = params.toString();
      router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [searchParams, router, pathname]
  );
  const [changes, setChanges] = useState<AssignmentChange[]>([]);
  const [loading, setLoading] = useState(false);

  // Navigate-mode picker: when user selects a snapshot, navigate to its page
  const currentRef = `${snapshot.date}/${snapshot.time}`;
  const handleNavigate = useCallback(
    (ref: string | null) => {
      if (!ref) return;
      const [navDate, navTime] = ref.split("/");
      router.push(`/day/${navDate}/${formatTime(navTime)}`);
    },
    [router]
  );

  const fetchAndDiff = useCallback(
    async (ref: string) => {
      setLoading(true);
      try {
        const [refDate, refTime] = ref.split("/");
        const timeFormatted = `${refTime.slice(0, 2)}:${refTime.slice(2, 4)}:${refTime.slice(4, 6)}`;
        const res = await fetch(
          `/api/snapshot/${refDate}/${timeFormatted}`
        );
        if (!res.ok) {
          setChanges([]);
          return;
        }
        const prevAssignments: Record<string, Assignment[]> = await res.json();

        const allChanges: AssignmentChange[] = [];
        for (const slug of slugs) {
          const curr = classAssignments[slug] || [];
          const prev = prevAssignments[slug] || [];
          allChanges.push(...diffAssignments(curr, prev, slug));
        }
        setChanges(allChanges);
      } catch {
        setChanges([]);
      } finally {
        setLoading(false);
      }
    },
    [classAssignments, slugs]
  );

  useEffect(() => {
    if (compareRef) {
      fetchAndDiff(compareRef);
    } else {
      setChanges([]);
    }
  }, [compareRef, fetchAndDiff]);

  const assignments = classAssignments[activeSlug] || [];
  const changeCount = changes.length;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <Link
          href="/"
          className="text-blue-500 hover:underline text-sm"
        >
          &larr; Calendar
        </Link>
        <div className="flex items-baseline gap-2 mt-1 flex-wrap">
          <h1 className="text-xl font-semibold">
            <SnapshotCalendarPicker
              mode="navigate"
              selectedRef={currentRef}
              onChange={handleNavigate}
              snapshots={allSnapshots}
            />
          </h1>
          {priorSnapshots.length > 0 && (
            <SnapshotCalendarPicker
              mode="compare"
              selectedRef={compareRef}
              onChange={setCompareRef}
              snapshots={priorSnapshots}
            />
          )}
        </div>
      </div>


      {/* Change summary */}
      {compareRef && changeCount > 0 && !loading && (
        <div className="text-sm text-gray-500">
          {changeCount} assignment change{changeCount !== 1 ? "s" : ""}
        </div>
      )}
      {compareRef && changeCount === 0 && !loading && (
        <div className="text-sm text-gray-500">No changes detected.</div>
      )}
      {loading && (
        <div className="text-sm text-gray-400">Loading comparison...</div>
      )}
      {!compareRef && priorSnapshots.length === 0 && (
        <div className="text-sm text-gray-500">
          This is the earliest snapshot.
        </div>
      )}
      {!compareRef && priorSnapshots.length > 0 && (
        <div className="text-sm text-gray-500">
          No comparison selected.
        </div>
      )}

      <ChangeLegend />

      <ClassTabs
        classes={snapshot.classes}
        activeSlug={activeSlug}
        onSelect={setActiveSlug}
        changes={changes}
      />

      <DiffTable
        assignments={assignments}
        changes={changes}
        slug={activeSlug}
      />
    </div>
  );
}
