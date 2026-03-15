"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import type { SnapshotEntry } from "@/lib/types";
import { toLocalDate } from "@/lib/format";
import { useLocalSnapshots } from "@/hooks/useLocalSnapshots";
import LocalDate from "@/components/LocalDate";
import LocalTime from "@/components/LocalTime";

const MONTH_NAMES = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const DAY_NAMES = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

interface SnapshotCalendarPickerProps {
  /** "navigate" shows date+time as trigger and navigates on select; "compare" shows "vs prior" label */
  mode: "navigate" | "compare";
  selectedRef: string | null;
  onChange: (ref: string | null) => void;
  snapshots: SnapshotEntry[];
}

export default function SnapshotCalendarPicker({
  mode,
  selectedRef,
  onChange,
  snapshots,
}: SnapshotCalendarPickerProps) {
  const [open, setOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const { mounted, byDate, latestLocalDate } = useLocalSnapshots(snapshots);

  // Determine which month to show
  const latest = snapshots[snapshots.length - 1];
  const [viewYear, setViewYear] = useState(() => {
    if (!latest) return new Date().getFullYear();
    return parseInt(latest.date.slice(0, 4));
  });
  const [viewMonth, setViewMonth] = useState(() => {
    if (!latest) return new Date().getMonth();
    return parseInt(latest.date.slice(5, 7)) - 1;
  });

  // Adjust view month to local date after mount
  useEffect(() => {
    if (latestLocalDate) {
      setViewYear(parseInt(latestLocalDate.slice(0, 4)));
      setViewMonth(parseInt(latestLocalDate.slice(5, 7)) - 1);
    }
  }, [latestLocalDate]);

  // Close on outside click
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  const [expandedDate, setExpandedDate] = useState<string | null>(null);

  const prevMonth = () => {
    if (viewMonth === 0) { setViewYear(viewYear - 1); setViewMonth(11); }
    else setViewMonth(viewMonth - 1);
  };
  const nextMonth = () => {
    if (viewMonth === 11) { setViewYear(viewYear + 1); setViewMonth(0); }
    else setViewMonth(viewMonth + 1);
  };

  const firstDay = new Date(viewYear, viewMonth, 1).getDay();
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();

  const cells: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  const selectedDate = useMemo(() => {
    if (!selectedRef) return null;
    const [refDate, refTime] = selectedRef.split("/");
    return mounted ? toLocalDate(refDate, refTime) : refDate;
  }, [selectedRef, mounted]);

  function handleDateClick(dateStr: string) {
    const snaps = byDate.get(dateStr);
    if (!snaps || snaps.length === 0) return;

    if (snaps.length === 1) {
      onChange(`${snaps[0].date}/${snaps[0].time}`);
      setExpandedDate(null);
      setOpen(false);
    } else {
      setExpandedDate(expandedDate === dateStr ? null : dateStr);
    }
  }

  function handleTimeClick(s: SnapshotEntry) {
    onChange(`${s.date}/${s.time}`);
    setExpandedDate(null);
    setOpen(false);
  }

  function handleClear() {
    onChange(null);
    setOpen(false);
  }

  const refDate = selectedRef ? selectedRef.split("/")[0] : null;
  const refTime = selectedRef ? selectedRef.split("/")[1] : null;

  return (
    <span className="text-xl font-semibold relative inline-flex items-baseline gap-1">
      {mode === "compare" && "vs prior "}
      <button
        onClick={() => setOpen(!open)}
        className="text-xl font-semibold text-blue-600 hover:text-blue-800 border-b-2 border-dashed border-blue-300 hover:border-blue-500 cursor-pointer"
      >
        {refDate && refTime ? (
          <><LocalDate time={refTime} date={refDate} />{" "}
          <LocalTime time={refTime} date={refDate} /></>
        ) : (
          "select"
        )}
      </button>

      {open && (
        <div
          ref={popoverRef}
          className="absolute top-full left-0 mt-2 z-50 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-3 w-72"
          style={{ fontWeight: "normal", fontSize: "14px" }}
        >
          {/* Month nav */}
          <div className="flex items-center justify-between mb-2">
            <button
              onClick={prevMonth}
              className="px-2 py-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              &larr;
            </button>
            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              {MONTH_NAMES[viewMonth]} {viewYear}
            </span>
            <button
              onClick={nextMonth}
              className="px-2 py-0.5 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-400"
            >
              &rarr;
            </button>
          </div>

          {/* Day headers */}
          <div className="grid grid-cols-7 gap-0 mb-1">
            {DAY_NAMES.map((d) => (
              <div
                key={d}
                className="text-center text-[10px] font-medium text-gray-400 py-0.5"
              >
                {d}
              </div>
            ))}
          </div>

          {/* Day cells */}
          <div className="grid grid-cols-7 gap-0">
            {cells.map((day, i) => {
              if (day === null) {
                return <div key={`e-${i}`} className="h-9" />;
              }

              const dateStr = `${viewYear}-${String(viewMonth + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
              const snaps = byDate.get(dateStr);
              const hasSnapshots = snaps && snaps.length > 0;
              const isSelected = dateStr === selectedDate;
              const snapCount = snaps?.length || 0;

              return (
                <button
                  key={dateStr}
                  onClick={() => hasSnapshots && handleDateClick(dateStr)}
                  disabled={!hasSnapshots}
                  className={`
                    h-9 w-full flex items-center justify-center rounded-full text-xs relative
                    ${hasSnapshots ? "cursor-pointer" : "cursor-default text-gray-300 dark:text-gray-600"}
                    ${isSelected ? "bg-blue-500 text-white font-bold" : ""}
                    ${hasSnapshots && !isSelected ? "text-gray-800 dark:text-gray-200 hover:bg-blue-100 dark:hover:bg-blue-900 font-medium" : ""}
                  `}
                >
                  {day}
                  {hasSnapshots && !isSelected && (
                    <span
                      className="absolute bottom-0.5 left-1/2 -translate-x-1/2 rounded-full bg-blue-400"
                      style={{
                        width: Math.min(4 + snapCount * 2, 10),
                        height: Math.min(4 + snapCount * 2, 10),
                      }}
                    />
                  )}
                </button>
              );
            })}
          </div>

          {/* Time list for expanded date */}
          {expandedDate && byDate.get(expandedDate) && (
            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700">
              <div className="text-xs font-semibold text-gray-500 mb-1">
                {expandedDate}
              </div>
              <div className="flex flex-wrap gap-1">
                {byDate.get(expandedDate)!.map((s) => {
                  const ref = `${s.date}/${s.time}`;
                  const isActive = ref === selectedRef;
                  return (
                    <button
                      key={ref}
                      onClick={() => handleTimeClick(s)}
                      className={`
                        px-2 py-1 rounded text-xs
                        ${isActive
                          ? "bg-blue-500 text-white font-medium"
                          : "bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-blue-100 dark:hover:bg-blue-900"
                        }
                      `}
                    >
                      <LocalTime time={s.time} date={s.date} />
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Clear button (compare mode only) */}
          {mode === "compare" && (
            <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-700 flex justify-end">
              <button
                onClick={handleClear}
                className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                Clear comparison
              </button>
            </div>
          )}
        </div>
      )}
    </span>
  );
}
