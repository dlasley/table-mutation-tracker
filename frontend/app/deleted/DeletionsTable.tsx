"use client";

import { useState, useMemo } from "react";
import type { DeletedAssignment } from "@/lib/types";

type SortCol = "className" | "first_seen" | "first_deleted";
type SortDir = "asc" | "desc";

function formatTimestamp(iso: string): string {
  if (!iso) return "--";
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatDueDate(dateStr: string): string {
  if (!dateStr) return "--";
  const [, m, d] = dateStr.split("-");
  return `${parseInt(m)}/${parseInt(d)}`;
}

function SortArrow({ col, sortCol, sortDir }: { col: SortCol; sortCol: SortCol; sortDir: SortDir }) {
  if (col !== sortCol) return <span className="text-gray-500 ml-0.5">{"\u21C5"}</span>;
  return <span className="ml-0.5">{sortDir === "asc" ? "\u25B2" : "\u25BC"}</span>;
}

export default function DeletionsTable({ deletions }: { deletions: DeletedAssignment[] }) {
  const [sortCol, setSortCol] = useState<SortCol>("first_deleted");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  function toggleSort(col: SortCol) {
    if (sortCol === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortCol(col);
      setSortDir("asc");
    }
  }

  const sorted = useMemo(() => {
    const copy = [...deletions];
    copy.sort((a, b) => {
      const av = a[sortCol];
      const bv = b[sortCol];
      const cmp = (av || "").localeCompare(bv || "");
      return sortDir === "asc" ? cmp : -cmp;
    });
    return copy;
  }, [deletions, sortCol, sortDir]);

  const thBase = "py-2 px-2 font-medium text-gray-500 cursor-pointer hover:text-gray-700 dark:hover:text-gray-300 select-none";

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className={`text-left ${thBase}`} onClick={() => toggleSort("className")}>
              Class <SortArrow col="className" sortCol={sortCol} sortDir={sortDir} />
            </th>
            <th className="text-left py-2 px-2 font-medium text-gray-500">Assignment</th>
            <th className="text-left py-2 px-2 font-medium text-gray-500">Due</th>
            <th className="text-left py-2 px-2 font-medium text-gray-500">Score</th>
            <th className="text-right py-2 px-2 font-medium text-gray-500">%</th>
            <th className="text-center py-2 px-2 font-medium text-gray-500">Grade</th>
            <th className={`text-left ${thBase}`} onClick={() => toggleSort("first_seen")}>
              First Seen <SortArrow col="first_seen" sortCol={sortCol} sortDir={sortDir} />
            </th>
            <th className={`text-left ${thBase}`} onClick={() => toggleSort("first_deleted")}>
              Deletion Detected <SortArrow col="first_deleted" sortCol={sortCol} sortDir={sortDir} />
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((d, i) => (
            <tr key={`${d.classSlug}-${d.assignment}-${d.due_date}-${i}`} className="border-b border-gray-100 dark:border-gray-800 bg-red-50/50 dark:bg-red-950/20">
              <td className="py-2 px-2">{d.className}</td>
              <td className="py-2 px-2">{d.assignment}</td>
              <td className="py-2 px-2 whitespace-nowrap">{formatDueDate(d.due_date)}</td>
              <td className="py-2 px-2 font-mono">{d.score_raw || "--"}</td>
              <td className="py-2 px-2 text-right font-mono">
                {d.percent != null ? `${d.percent}` : "--"}
              </td>
              <td className="py-2 px-2 text-center font-medium">{d.grade ?? "--"}</td>
              <td className="py-2 px-2 whitespace-nowrap text-gray-500">{formatTimestamp(d.first_seen)}</td>
              <td className="py-2 px-2 whitespace-nowrap text-red-600 dark:text-red-400">{formatTimestamp(d.first_deleted)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
