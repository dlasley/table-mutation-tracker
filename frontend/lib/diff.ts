import type { Assignment, AssignmentChange, FieldChange } from "./types";

const DIFF_FIELDS = [
  "category",
  "score_raw",
  "percent",
  "grade",
  "has_comments",
] as const;

/** Compute assignment-level changes between two snapshots for one class. */
export function diffAssignments(
  current: Assignment[],
  previous: Assignment[],
  slug: string
): AssignmentChange[] {
  const prevByKey = new Map<string, Assignment>();
  for (const a of previous) {
    prevByKey.set(`${a.name}|${a.due_date}`, a);
  }
  const currByKey = new Map<string, Assignment>();
  for (const a of current) {
    currByKey.set(`${a.name}|${a.due_date}`, a);
  }

  const changes: AssignmentChange[] = [];

  // Added
  for (const [key, a] of currByKey) {
    if (!prevByKey.has(key)) {
      changes.push({
        class: slug,
        assignment: a.name,
        due_date: a.due_date,
        type: "added",
      });
    }
  }

  // Deleted
  for (const [key, a] of prevByKey) {
    if (!currByKey.has(key)) {
      changes.push({
        class: slug,
        assignment: a.name,
        due_date: a.due_date,
        type: "deleted",
      });
    }
  }

  // Modified
  for (const [key, curr] of currByKey) {
    const prev = prevByKey.get(key);
    if (!prev) continue;

    const fieldChanges: FieldChange[] = [];
    for (const field of DIFF_FIELDS) {
      const oldVal = prev[field];
      const newVal = curr[field];
      if (oldVal !== newVal) {
        fieldChanges.push({ field, old: oldVal ?? null, new: newVal ?? null });
      }
    }

    if (fieldChanges.length > 0) {
      changes.push({
        class: slug,
        assignment: curr.name,
        due_date: curr.due_date,
        type: "modified",
        changes: fieldChanges,
      });
    }
  }

  return changes;
}
