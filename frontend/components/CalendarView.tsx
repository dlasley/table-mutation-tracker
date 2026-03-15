"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import type { SnapshotEntry } from "@/lib/types";
import { formatTime } from "@/lib/format";
import { useLocalSnapshots } from "@/hooks/useLocalSnapshots";

interface CalendarViewProps {
  snapshots: SnapshotEntry[];
  initialYear: number;
  initialMonth: number;
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

const DAY_NAMES = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export default function CalendarView({
  snapshots,
  initialYear,
  initialMonth,
}: CalendarViewProps) {
  const [year, setYear] = useState(initialYear);
  const [month, setMonth] = useState(initialMonth);
  const { latestByDate, latestLocalDate } = useLocalSnapshots(snapshots);

  // Adjust view month to the latest snapshot's local date after mount
  useEffect(() => {
    if (latestLocalDate) {
      setYear(parseInt(latestLocalDate.slice(0, 4)));
      setMonth(parseInt(latestLocalDate.slice(5, 7)) - 1);
    }
  }, [latestLocalDate]);

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  const prevMonth = () => {
    if (month === 0) { setYear(year - 1); setMonth(11); }
    else setMonth(month - 1);
  };

  const nextMonth = () => {
    if (month === 11) { setYear(year + 1); setMonth(0); }
    else setMonth(month + 1);
  };

  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <button onClick={prevMonth} className="px-3 py-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-lg">
          &larr;
        </button>
        <h2 className="text-xl font-semibold">
          {MONTH_NAMES[month]} {year}
        </h2>
        <button onClick={nextMonth} className="px-3 py-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-lg">
          &rarr;
        </button>
      </div>

      {/* Day headers */}
      <div className="grid grid-cols-7 gap-1 mb-1">
        {DAY_NAMES.map((d) => (
          <div key={d} className="text-center text-xs font-medium text-gray-500 py-1">
            {d}
          </div>
        ))}
      </div>

      {/* Day cells */}
      <div className="grid grid-cols-7 gap-1">
        {cells.map((day, i) => {
          if (day === null) {
            return <div key={`empty-${i}`} className="h-24" />;
          }

          const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
          const snap = latestByDate.get(dateStr);

          return (
            <DayCell key={dateStr} day={day} snapshot={snap} />
          );
        })}
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-4 text-xs text-gray-500 justify-center">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-600 inline-block" /> No data</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-green-100 dark:bg-green-900 inline-block" /> No changes</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-yellow-100 dark:bg-yellow-900 inline-block" /> Added</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-orange-100 dark:bg-orange-900 inline-block" /> Changed</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-100 dark:bg-red-900 inline-block" /> Deleted</span>
      </div>
    </div>
  );
}

function DayCell({
  day,
  snapshot,
}: {
  day: number;
  snapshot: SnapshotEntry | undefined;
}) {
  if (!snapshot) {
    return (
      <div className="h-24 rounded border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-1">
        <span className="text-xs text-gray-400">{day}</span>
      </div>
    );
  }

  const { changes } = snapshot;
  let bgColor = "bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800";

  if (changes.deleted > 0) {
    bgColor = "bg-red-50 dark:bg-red-950 border-red-200 dark:border-red-800";
  } else if (changes.modified > 0) {
    bgColor = "bg-orange-50 dark:bg-orange-950 border-orange-200 dark:border-orange-800";
  } else if (changes.added > 0) {
    bgColor = "bg-yellow-50 dark:bg-yellow-950 border-yellow-200 dark:border-yellow-800";
  }

  return (
    <Link href={`/day/${snapshot.date}/${formatTime(snapshot.time)}`}>
      <div className={`h-24 rounded border ${bgColor} p-1 hover:ring-2 hover:ring-blue-400 cursor-pointer transition-all`}>
        <span className="text-xs font-medium">{day}</span>
        {changes.total > 0 && (
          <div className="mt-1 text-xs space-y-0.5">
            {changes.added > 0 && (
              <div className="text-yellow-700 dark:text-yellow-400">+{changes.added} added</div>
            )}
            {changes.modified > 0 && (
              <div className="text-orange-700 dark:text-orange-400">{changes.modified} changed</div>
            )}
            {changes.deleted > 0 && (
              <div className="text-red-700 dark:text-red-400">-{changes.deleted} deleted</div>
            )}
          </div>
        )}
        {changes.total === 0 && (
          <div className="mt-1 text-xs text-green-600 dark:text-green-400">No changes</div>
        )}
      </div>
    </Link>
  );
}
