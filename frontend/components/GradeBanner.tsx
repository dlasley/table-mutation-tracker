"use client";

import { gradeColor } from "@/lib/format";
import type { ClassSummary } from "@/lib/types";

interface GradeBannerProps {
  classes: Record<string, ClassSummary>;
  gpa?: number | null;
}

export default function GradeBanner({ classes, gpa }: GradeBannerProps) {
  return (
    <div className="space-y-3">
      {gpa != null && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">GPA</span>
          <span className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {gpa.toFixed(2)}
          </span>
        </div>
      )}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {Object.entries(classes).map(([slug, cls]) => (
          <div
            key={slug}
            className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-center"
          >
            <div className="text-xs text-gray-500 truncate">{cls.course}</div>
            <div className={`text-2xl font-bold ${gradeColor(cls.final_grade)}`}>
              {cls.final_grade ?? "--"}
            </div>
            <div className="text-xs text-gray-400">
              {cls.final_percent != null ? `${cls.final_percent}%` : "--"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
