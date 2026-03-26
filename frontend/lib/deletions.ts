import type { DeletedAssignment, SnapshotEntry } from "./types";
import { loadRollingIndex, loadAssignments } from "./snapshots";
import { diffAssignments } from "./diff";

/**
 * Compute all assignment deletions across all snapshots.
 *
 * Pass 1: Find snapshots with deletions, diff against their previous snapshot
 *         to identify which assignments were deleted and capture their details.
 * Pass 2: For each deleted assignment, binary search backwards to find the
 *         earliest snapshot where it first appeared.
 */
export async function computeDeletions(): Promise<DeletedAssignment[]> {
  const index = await loadRollingIndex();
  const snapshots = index.snapshots;

  // Pass 1: Find all deletions with details
  const deletions: DeletedAssignment[] = [];

  for (const snap of snapshots) {
    if (snap.changes.deleted === 0 || !snap.previous_snapshot) continue;

    const [prevDate, prevTime] = snap.previous_snapshot.split("/");
    const slugs = Object.keys(snap.classes);

    // Load assignments for both snapshots across all classes in parallel
    const [currentBySlug, previousBySlug] = await Promise.all([
      loadAllClasses(snap.date, snap.time, slugs),
      loadAllClasses(prevDate, prevTime, slugs),
    ]);

    for (const slug of slugs) {
      const current = currentBySlug.get(slug) || [];
      const previous = previousBySlug.get(slug) || [];
      const changes = diffAssignments(current, previous, slug);

      for (const change of changes) {
        if (change.type !== "deleted") continue;

        // Get full assignment details from previous snapshot
        const prevAssignment = previous.find(
          (a) => a.name === change.assignment && a.due_date === change.due_date
        );

        deletions.push({
          className: snap.classes[slug]?.course || slug,
          classSlug: slug,
          assignment: change.assignment,
          due_date: change.due_date,
          score_raw: prevAssignment?.score_raw || "",
          grade: prevAssignment?.grade ?? null,
          percent: prevAssignment?.percent ?? null,
          first_seen: "", // filled in Pass 2
          first_deleted: snap.scrape_timestamp,
        });
      }
    }
  }

  // Pass 2: Find first appearance of each deleted assignment
  for (const del of deletions) {
    del.first_seen = await findFirstSeen(
      snapshots,
      del.classSlug,
      del.assignment,
      del.due_date,
      del.first_deleted
    );
  }

  // Sort by first_deleted ascending
  deletions.sort((a, b) => a.first_deleted.localeCompare(b.first_deleted));

  return deletions;
}

async function loadAllClasses(
  date: string,
  time: string,
  slugs: string[]
): Promise<Map<string, Awaited<ReturnType<typeof loadAssignments>>>> {
  const entries = await Promise.all(
    slugs.map(async (slug) => {
      const assignments = await loadAssignments(date, time, slug);
      return [slug, assignments] as const;
    })
  );
  return new Map(entries);
}

/**
 * Binary search backwards through snapshots to find the earliest one
 * containing the given assignment.
 */
async function findFirstSeen(
  snapshots: SnapshotEntry[],
  slug: string,
  name: string,
  due_date: string,
  deletedTimestamp: string
): Promise<string> {
  // Find the index of the snapshot just before deletion
  const deletionIdx = snapshots.findIndex(
    (s) => s.scrape_timestamp === deletedTimestamp
  );
  if (deletionIdx <= 0) return snapshots[0]?.scrape_timestamp || deletedTimestamp;

  // The assignment existed in the previous snapshot (that's where we found it)
  // Binary search: find the earliest snapshot index where the assignment exists
  let lo = 0;
  let hi = deletionIdx - 1;
  let earliest = hi; // We know it exists at hi (the snapshot before deletion)

  while (lo <= hi) {
    const mid = Math.floor((lo + hi) / 2);
    const snap = snapshots[mid];
    const exists = await assignmentExists(snap.date, snap.time, slug, name, due_date);

    if (exists) {
      earliest = mid;
      hi = mid - 1;
    } else {
      lo = mid + 1;
    }
  }

  return snapshots[earliest].scrape_timestamp;
}

async function assignmentExists(
  date: string,
  time: string,
  slug: string,
  name: string,
  due_date: string
): Promise<boolean> {
  const assignments = await loadAssignments(date, time, slug);
  return assignments.some((a) => a.name === name && a.due_date === due_date);
}
