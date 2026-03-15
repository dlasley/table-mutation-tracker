# Table Mutation Tracker
_Automated Change Detection for Student Information Systems_

A system that scrapes a Student Information System (SIS) parent portal on a schedule, detects changes to assignment and grade data, including retroactive modifications, and surfaces those changes through a calendar-based diff UI. UI inspired by https://archive.org.

Built to solve a real-world problem: Student Information Systems are inherently ephemeral. Updates made retroactively by a teacher are not surfaced as a time series, leaving parents and students to detect changes through manually timestamped screenshots or spreadsheets. Git history provides the audit trail natively, as every snapshot is an immutable, timestamped commit.

## Architecture

The system is decomposed into four isolated runtime boundaries deployed across n8n, a container runtime, GitHub, and Vercel. Each has a single responsibility and no access to credentials it does not need.

```text
                    ┌──────────────────────────────────────────────┐
                    │                ORCHESTRATION                 │
                    │                     n8n                      │
                    │                                              │
                    │  Scheduling · Dispatch · Conditional logic   │
                    │  Credential management · Delivery routing    │
                    │                                              │
                    │  (see Control Plane Workflow.jpg)            │
                    └──┬──────────────┬───────────────────┬────────┘
                       │              │                   │
         POST /scrape  │  GitHub API  │           Email,  │
           IAM + HMAC  │    (commit)  │      Slack, etc.  │
                       ▼              ▼                   ▼
┌────────────────────────┐ ┌────────────────────────┐ ┌────────────────────┐
│   COLLECTION + INDEX   │ │     STORAGE            │ │     MESSAGING      │
│   Container Runtime    │ │     GitHub             │ │     n8n-native     │
│                        │ │                        │ │                    │
│  Headless browser      │ │  Private repo          │ │  Email             │
│  scraping SIS portal   │ │  (data snapshots only) │ │  Future channels   │
│                        │ │                        │ │                    │
│  -POST /scrape:        │ │  -Code and data        │ │  -n8n routes to    │
│   stateless worker,    │ │   repos separated      │ │   channels based   │
│   returns JSON         │ │  -Git history =        │ │   on change type   │
│  -POST /rebuild-index: │ │   full audit log       │ │                    │
│   diffs snapshots,     │ │                        │ │                    │
│   writes rolling index │ │                        │ │                    │
└────────────────────────┘ └────────┬───────────────┘ └────────────────────┘
                                    │
                        GitHub API  │ (read-only)
                                    ▼
                         ┌──────────────────────┐
                         │    PRESENTATION      │
                         │       Vercel         │
                         │                      │
                         │  -Calendar UI        │
                         │  -Client-side diffs  │
                         │  -SSR from storage   │
                         └──────────────────────┘
```

### n8n as the Control Plane

n8n owns the entire data flow. The scraper is a stateless worker that returns JSON -- it knows nothing about where data goes or who gets notified. n8n decides what happens with the results: commit to GitHub, notify on changes, retry on failure, route alerts and status notifications via email, with additional messaging channels available as workflow branches.

This is a deliberate separation. The scraper's job is to collect. n8n's job is to orchestrate. Neither holds responsibility for the other's concerns.

![n8n Daily Scrape Pipeline](n8n/Control%20Plane%20Workflow.jpg)

**Workflow**: Schedule Trigger &rarr; POST /scrape to scraper &rarr; success/failure branch &rarr; split class snapshots &rarr; commit each to GitHub &rarr; update snapshot metadata &rarr; diff snapshots (n8n Code nodes) &rarr; update rolling index &rarr; notify on error

### Collection + Index: Containerized Scraper

A Python + Playwright service behind FastAPI with two endpoints:

- **POST /scrape**: Stateless scraper. Logs into the SIS portal, extracts assignment tables, returns normalized JSON. Knows nothing about storage or delivery.
- **POST /rebuild-index**: Reads all snapshots from the data repo, diffs consecutive pairs, and writes a rolling index with accurate change counts. Called by n8n after each scrape, or manually for backfills.

The scraper implements a `TableSource` abstraction so additional SIS platforms can be added without changing the orchestration layer.

```text
SISSource(TableSource)    <- current implementation
FutureSource(TableSource) <- swap in without touching n8n
```

Authentication is HMAC-based: n8n signs each request with a shared webhook secret, which the scraper verifies before processing.

### Storage: Two-Repo Separation

Code and data live in separate repositories:
- **table-mutation-tracker** (this repo): Application code, public-ready
- **table-mutation-data** (private): Snapshot JSON and rolling index only

The data repo receives commits exclusively through n8n via the GitHub Contents API. Git history serves as a complete audit trail of every change detected.

```text
snapshots/
  2026-03-10/
    140532/
      english_10/assignments.json
      algebra_2/assignments.json
      metadata.json
index/
  rolling_index.json
```

### Presentation: Dual-Layer Diffing

A Next.js app on Vercel reads snapshots from the data repo via GitHub API. Change detection happens at two levels:

- **Rolling index** (pre-computed): n8n's Code nodes diff each new snapshot against its predecessor and store change counts in the rolling index. The calendar view reads these counts to color-code days without fetching individual snapshots.
- **Detail view** (client-side): When a user clicks a day, the frontend fetches both snapshots and diffs them field-by-field, classifying changes as added, deleted, graded, or modified.

This keeps the frontend fully decoupled from both the scraper and n8n. It reads from storage and nothing else.

### Messaging: Notification Routing

n8n handles all outbound communication. Error notifications are active today: email on scrape failure, and a global workspace error handler following n8n design patterns. The architecture supports adding channels (Slack, SMS, weekly digests) as n8n workflow branches without touching any application code.

## Project Structure

```text
table-mutation-tracker/
├── src/
│   ├── main.py              # Scrape orchestration (called by webhook)
│   ├── webhook.py           # FastAPI endpoints: /scrape, /rebuild-index, /health
│   ├── config.py            # Config loader (sources.json + env vars)
│   ├── lib/
│   │   ├── snapshot_store.py  # SnapshotStore ABC + diff logic
│   │   └── github_store.py   # GitHub Contents API implementation
│   └── scraper/
│       ├── base.py          # TableSource ABC, Assignment/ClassSnapshot models
│       ├── sis.py           # SIS portal implementation
│       └── normalize.py     # Date, score, grade normalization
├── frontend/
│   ├── app/                 # Next.js App Router (calendar + day views)
│   ├── components/          # CalendarView, DiffTable, ClassTabs, GradeBanner
│   ├── lib/
│   │   ├── diff.ts          # Client-side assignment diffing engine
│   │   ├── snapshots.ts     # GitHub API data fetching
│   │   └── types.ts         # Shared TypeScript types
│   └── hooks/               # Local snapshot state management
├── config/
│   └── sources.json         # SIS URLs and class definitions
├── scripts/
│   ├── generate_synthetic.py  # Test data generator (--days N, pushes to data repo)
│   └── rebuild_index.py       # CLI to rebuild rolling index from existing snapshots
├── Dockerfile               # Playwright + Chromium containerized scraper
├── docker-compose.yml       # Caddy + n8n deployment (GCE)
└── Caddyfile                # Reverse proxy + auto-TLS for n8n
```

## Environment Configuration

### Scraper

| Variable | Description |
|---|---|
| `SIS_USERNAME`   | SIS portal credentials |
| `SIS_PASSWORD`   | SIS portal credentials |
| `WEBHOOK_SECRET` | Shared secret for n8n request verification |
| `GITHUB_TOKEN`   | Fine-grained PAT with read/write access to data repo (used by `/rebuild-index`) |
| `DATA_REPO`      | GitHub data repo (`owner/repo` format, used by `/rebuild-index`) |

### Vercel (Frontend)

| Variable       | Description |
|----------------|-------------|
| `GITHUB_TOKEN` | Fine-grained PAT with read access to data repo |
| `DATA_REPO`    | GitHub data repo (`owner/repo` format) |
| `DATA_PREFIX`  | Namespace for data paths. Empty for production, `synthetic` for preview deployments |
| `BASIC_AUTH_CREDENTIALS` | Single `user:pass` for HTTP basic auth. Scope per environment in Vercel. Unset = no auth |

### n8n + Caddy

| Variable       | Description         |
|----------------|---------------------|
| `N8N_USER`     | Basic auth username |
| `N8N_PASSWORD` | Basic auth password |

All remaining credentials (GitHub PAT, webhook secret, SIS credentials for passthrough) are stored in n8n's encrypted credential store.

## Getting Started

### Prerequisites

- Docker
- A container runtime that can serve HTTP (Cloud Run, App Runner, Fly.io, or similar)
- A container registry accessible from your runtime
- GitHub fine-grained PAT with Contents read/write on the data repo
- n8n instance (self-hosted or cloud)

### Scraper Deployment

```bash
# Build for linux/amd64 (required for Playwright/Chromium)
docker buildx build --platform linux/amd64 -t <your-registry>/table-scraper:latest .

# Push to your registry and deploy to your container runtime
docker push <your-registry>/table-scraper:latest
```

### n8n + Caddy Deployment

```bash
cp .env.example .env
# Fill in N8N_USER, N8N_PASSWORD
docker compose up -d
```

### Frontend

Deployed via Vercel with auto-deploy from this repo. Set `GITHUB_TOKEN`, `DATA_REPO`, and `DATA_PREFIX` in Vercel environment settings.

## Development Philosophy

Built using AI-assisted development tooling while maintaining human ownership of architectural decisions, runtime separation, and governance design. AI accelerated implementation; system decomposition and operationalization patterns were deliberate and human-directed.

The focus throughout:
- n8n as orchestrator. It owns the data flow; workers are stateless.
- Runtime isolation over monolithic convenience. Each component scales, fails, and deploys independently.
- Credential isolation by boundary. No component holds secrets it does not need.
- Computed over stored. The rolling index pre-computes change counts for monthly calendar view performance, but detail-level diffs are always derived at read time from raw snapshots.
