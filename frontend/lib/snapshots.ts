import type {
  RollingIndex,
  Assignment,
} from "./types";

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || "";
const DATA_REPO = process.env.DATA_REPO || "dlasley/table-mutation-data";
const DATA_PREFIX = process.env.DATA_PREFIX || "";

// Build prefixed paths: "snapshots" or "snapshots/synthetic"
const SNAPSHOT_BASE = DATA_PREFIX ? `snapshots/${DATA_PREFIX}` : "snapshots";
const INDEX_BASE = DATA_PREFIX ? `index/${DATA_PREFIX}` : "index";

export class GitHubError extends Error {
  constructor(
    readonly status: number,
    filePath: string
  ) {
    super(`GitHub API ${status}: ${filePath}`);
    this.name = "GitHubError";
  }
}

async function fetchGitHub(filePath: string): Promise<string> {
  const url = `https://api.github.com/repos/${DATA_REPO}/contents/${filePath}`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      Accept: "application/vnd.github.raw+json",
    },
    next: { revalidate: 60 },
  });
  if (!res.ok) {
    throw new GitHubError(res.status, filePath);
  }
  return res.text();
}

export async function loadRollingIndex(): Promise<RollingIndex> {
  const raw = await fetchGitHub(`${INDEX_BASE}/rolling_index.json`);
  return JSON.parse(raw);
}

export async function loadAssignments(
  date: string,
  time: string,
  slug: string
): Promise<Assignment[]> {
  try {
    const raw = await fetchGitHub(`${SNAPSHOT_BASE}/${date}/${time}/${slug}/assignments.json`);
    return JSON.parse(raw);
  } catch (err) {
    // Only a missing file means the class is absent from this snapshot.
    if (err instanceof GitHubError && err.status === 404) return [];
    throw err;
  }
}
