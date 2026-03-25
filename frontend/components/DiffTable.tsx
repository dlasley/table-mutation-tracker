"use client";

import { useState, useCallback } from "react";
import type { Assignment, AssignmentChange, FieldChange } from "@/lib/types";

interface DiffTableProps {
  assignments: Assignment[];
  changes: AssignmentChange[];
  slug: string;
}

function copyTableToClipboard(assignments: Assignment[]) {
  const headers = ["Due Date", "Category", "Assignment", "Score", "%", "Grade"];

  const rows = assignments.map((a) => [
    formatDate(a.due_date),
    a.category,
    a.name,
    a.score_raw,
    a.percent != null ? String(a.percent) : "",
    a.grade ?? "",
  ]);

  // Tab-separated for Sheets/Excel
  const tsv = [headers, ...rows].map((r) => r.join("\t")).join("\n");

  // HTML table for rich-text paste (email clients)
  const cellStyle = 'style="border:1px solid #ccc;padding:4px 8px"';
  const headerStyle = 'style="border:1px solid #ccc;padding:4px 8px;font-weight:bold;background:#f5f5f5"';
  const htmlRows = rows
    .map((r) => `<tr>${r.map((c) => `<td ${cellStyle}>${c}</td>`).join("")}</tr>`)
    .join("");
  const html = `<table style="border-collapse:collapse"><thead><tr>${headers.map((h) => `<th ${headerStyle}>${h}</th>`).join("")}</tr></thead><tbody>${htmlRows}</tbody></table>`;

  const blob = new Blob([html], { type: "text/html" });
  const textBlob = new Blob([tsv], { type: "text/plain" });

  navigator.clipboard.write([
    new ClipboardItem({
      "text/html": blob,
      "text/plain": textBlob,
    }),
  ]);
}

export default function DiffTable({ assignments, changes, slug }: DiffTableProps) {
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const changesByKey = new Map<string, AssignmentChange>();
  for (const c of changes) {
    if (c.class === slug) {
      changesByKey.set(`${c.assignment}|${c.due_date}`, c);
    }
  }

  const handleCopy = useCallback(() => {
    copyTableToClipboard(assignments);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }, [assignments]);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700">
            <th className="text-left py-2 px-2 font-medium text-gray-500 w-8"></th>
            <th className="text-left py-2 px-2 font-medium text-gray-500">Due Date</th>
            <th className="text-left py-2 px-2 font-medium text-gray-500">Category</th>
            <th className="text-left py-2 px-2 font-medium text-gray-500">Assignment</th>
            <th className="text-left py-2 px-2 font-medium text-gray-500">Score</th>
            <th className="text-right py-2 px-2 font-medium text-gray-500">%</th>
            <th className="text-center py-2 px-2 font-medium text-gray-500">Grade</th>
            <th className="py-2 px-2 w-10">
              <button
                onClick={handleCopy}
                title="Copy table to clipboard"
                className={`flex items-center justify-center w-7 h-7 rounded transition-colors ${
                  copied
                    ? "bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400"
                    : "bg-gray-100 text-gray-500 hover:bg-blue-100 hover:text-blue-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-blue-900/40 dark:hover:text-blue-400"
                }`}
              >
                {copied ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          {assignments.map((a) => {
            const key = `${a.name}|${a.due_date}`;
            const change = changesByKey.get(key);
            const isExpanded = expandedRow === key;
            const hasChange = !!change;

            return (
              <AssignmentRow
                key={key}
                assignment={a}
                change={change}
                isExpanded={isExpanded}
                onToggle={() => setExpandedRow(isExpanded ? null : key)}
                hasChange={hasChange}
              />
            );
          })}

          {/* Deleted assignments (not in current list) */}
          {changes
            .filter((c) => c.class === slug && c.type === "deleted")
            .map((c) => (
              <tr key={`del-${c.assignment}|${c.due_date}`} className="bg-red-50 dark:bg-red-950/30 border-b border-gray-100 dark:border-gray-800" title="Assignment was present in previous snapshot but is now gone">
                <td className="py-2 px-2 text-red-500 text-center">-</td>
                <td className="py-2 px-2 line-through text-gray-400">{formatDate(c.due_date)}</td>
                <td className="py-2 px-2 text-gray-400">--</td>
                <td className="py-2 px-2 line-through text-gray-400">{c.assignment}</td>
                <td className="py-2 px-2 text-gray-400" colSpan={4}>
                  <span className="text-red-600 dark:text-red-400 text-xs font-medium">DELETED</span>
                </td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

function AssignmentRow({
  assignment,
  change,
  isExpanded,
  onToggle,
  hasChange,
}: {
  assignment: Assignment;
  change: AssignmentChange | undefined;
  isExpanded: boolean;
  onToggle: () => void;
  hasChange: boolean;
}) {
  let rowBg = "";
  let indicator = "";
  if (change?.type === "added") {
    rowBg = "bg-green-50 dark:bg-green-950/30";
    indicator = "+";
  } else if (change?.type === "modified") {
    rowBg = "bg-orange-50 dark:bg-orange-950/30";
    indicator = "~";
  }

  return (
    <>
      <tr
        className={`border-b border-gray-100 dark:border-gray-800 ${rowBg} ${hasChange ? "cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800" : ""}`}
        onClick={hasChange ? onToggle : undefined}
        title={change?.type === "added" ? "New assignment (click to expand)" : change?.type === "modified" ? "Changed since last snapshot (click to expand)" : undefined}
      >
        <td className={`py-2 px-2 text-center ${change?.type === "added" ? "text-green-500" : change?.type === "modified" ? "text-orange-500" : "text-gray-300"}`}>
          {indicator}
        </td>
        <td className="py-2 px-2 whitespace-nowrap">{formatDate(assignment.due_date)}</td>
        <td className="py-2 px-2 text-gray-500">{assignment.category}</td>
        <td className="py-2 px-2">{assignment.name}</td>
        <td className="py-2 px-2 font-mono">{assignment.score_raw}</td>
        <td className="py-2 px-2 text-right font-mono">
          {assignment.percent != null ? `${assignment.percent}` : "--"}
        </td>
        <td className="py-2 px-2 text-center font-medium">
          {assignment.grade ?? "--"}
        </td>
        <td></td>
      </tr>

      {isExpanded && change?.type === "modified" && change.changes && (
        <tr className="bg-orange-50/50 dark:bg-orange-950/20">
          <td colSpan={8} className="px-6 py-2">
            <ChangeDetails changes={change.changes} />
          </td>
        </tr>
      )}

      {isExpanded && change?.type === "added" && (
        <tr className="bg-green-50/50 dark:bg-green-950/20">
          <td colSpan={8} className="px-6 py-2 text-xs text-green-700 dark:text-green-400">
            New assignment added in this snapshot.
          </td>
        </tr>
      )}
    </>
  );
}

function ChangeDetails({ changes }: { changes: FieldChange[] }) {
  return (
    <div className="text-xs space-y-1">
      {changes.map((c, i) => (
        <div key={i} className="flex items-center gap-2">
          <span className="font-medium text-gray-500 w-24">{c.field}:</span>
          <span className="line-through text-red-500">
            {c.old != null ? String(c.old) : "--"}
          </span>
          <span className="text-gray-400">&rarr;</span>
          <span className="font-medium text-green-600 dark:text-green-400">
            {c.new != null ? String(c.new) : "--"}
          </span>
        </div>
      ))}
    </div>
  );
}

function formatDate(dateStr: string): string {
  if (!dateStr) return "--";
  const [y, m, d] = dateStr.split("-");
  return `${parseInt(m)}/${parseInt(d)}`;
}
