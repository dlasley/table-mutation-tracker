/** Format a UTC date + HHMMSS time to the browser's local time. */
export function formatTime(time: string, date?: string): string {
  if (date) {
    const hh = time.slice(0, 2);
    const mm = time.slice(2, 4);
    const ss = time.slice(4, 6);
    const utc = new Date(`${date}T${hh}:${mm}:${ss}Z`);
    return utc.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true });
  }
  return `${time.slice(0, 2)}:${time.slice(2, 4)}:${time.slice(4, 6)}`;
}

/** Build a URL path for a specific snapshot. */
export function timeToUrl(date: string, time: string): string {
  return `/day/${date}/${formatTime(time)}`;
}

/** Format a previous_snapshot ref like "2026-03-05/101136" to "2026-03-05 4:11:36 PM". */
export function formatSnapshotRef(ref: string): string {
  const [date, time] = ref.split("/");
  return `${date} ${formatTime(time, date)}`;
}

/** Convert a UTC date + HHMMSS time to the browser's local YYYY-MM-DD date string. */
export function toLocalDate(date: string, time: string): string {
  const hh = time.slice(0, 2);
  const mm = time.slice(2, 4);
  const ss = time.slice(4, 6);
  const utc = new Date(`${date}T${hh}:${mm}:${ss}Z`);
  const y = utc.getFullYear();
  const m = String(utc.getMonth() + 1).padStart(2, "0");
  const d = String(utc.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Return a Tailwind text color class for a letter grade. */
export function gradeColor(grade: string | null): string {
  if (!grade) return "text-gray-400";
  if (grade.startsWith("A")) return "text-green-600 dark:text-green-400";
  if (grade.startsWith("B")) return "text-blue-600 dark:text-blue-400";
  if (grade.startsWith("C")) return "text-yellow-600 dark:text-yellow-400";
  if (grade.startsWith("D")) return "text-orange-600 dark:text-orange-400";
  return "text-red-600 dark:text-red-400";
}
