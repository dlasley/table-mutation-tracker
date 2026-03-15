"use client";

import { useSuperUser } from "./SuperUserProvider";
import { gradeColor } from "@/lib/format";
import type { ClassSummary, AssignmentChange } from "@/lib/types";

interface ClassTabsProps {
  classes: Record<string, ClassSummary>;
  activeSlug: string;
  onSelect: (slug: string) => void;
  changes?: AssignmentChange[];
}

export default function ClassTabs({ classes, activeSlug, onSelect, changes = [] }: ClassTabsProps) {
  const superUser = useSuperUser();

  // Per-class change counts
  const countsBySlug = new Map<string, { added: number; modified: number; deleted: number }>();
  for (const c of changes) {
    const counts = countsBySlug.get(c.class) || { added: 0, modified: 0, deleted: 0 };
    if (c.type === "added") counts.added++;
    else if (c.type === "modified") counts.modified++;
    else if (c.type === "deleted") counts.deleted++;
    countsBySlug.set(c.class, counts);
  }

  return (
    <div className="flex flex-wrap gap-1 border-b border-gray-200 dark:border-gray-700">
      {Object.entries(classes).map(([slug, cls]) => {
        const isActive = slug === activeSlug;
        const counts = countsBySlug.get(slug);
        return (
          <button
            key={slug}
            onClick={() => onSelect(slug)}
            className={`px-3 py-2 text-sm rounded-t transition-colors ${
              isActive
                ? "bg-white dark:bg-gray-800 border border-b-0 border-gray-200 dark:border-gray-700 font-medium"
                : "text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
            }`}
          >
            {cls.course}
            {superUser && (
              <span className={`ml-1.5 font-bold ${gradeColor(cls.final_grade)}`}>
                {cls.final_grade ?? "--"}
              </span>
            )}
            {counts && (
              <span className="ml-1.5 text-xs font-mono">
                {counts.added > 0 && (
                  <span className="text-green-600 dark:text-green-400">
                    +{counts.added}
                  </span>
                )}
                {counts.modified > 0 && (
                  <span className={counts.added > 0 ? "ml-1 text-orange-500" : "text-orange-500"}>
                    ~{counts.modified}
                  </span>
                )}
                {counts.deleted > 0 && (
                  <span className={counts.added + counts.modified > 0 ? "ml-1 text-red-500" : "text-red-500"}>
                    -{counts.deleted}
                  </span>
                )}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
