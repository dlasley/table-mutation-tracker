export interface ChangeSummary {
  class_level: number;
  added: number;
  modified: number;
  deleted: number;
  total: number;
}

export interface ClassSummary {
  course: string;
  final_grade: string | null;
  final_percent: number | null;
  assignment_count: number;
}

export interface SnapshotEntry {
  date: string;
  time: string;
  scrape_timestamp: string;
  previous_snapshot: string | null;
  changes: ChangeSummary;
  classes: Record<string, ClassSummary>;
}

export interface RollingIndex {
  snapshots: SnapshotEntry[];
}

export interface FieldChange {
  field: string;
  old: string | number | boolean | null;
  new: string | number | boolean | null;
}

export interface AssignmentChange {
  class: string;
  assignment: string;
  due_date: string;
  type: "added" | "modified" | "deleted";
  changes?: FieldChange[];
}

export interface Assignment {
  name: string;
  due_date: string;
  category: string;
  score_raw: string;
  points_earned: number | null;
  points_possible: number | null;
  percent: number | null;
  grade: string | null;
  has_comments: boolean;
  flags: Record<string, boolean>;
}
