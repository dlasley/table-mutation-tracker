# LiveKit Voice/Text Agent Integration

This document tracks the integration of a LiveKit voice/text agent widget into the table-mutation-tracker frontend.

## Overview

A LiveKit-powered agent ("Sally") allows users to ask questions about their grades, assignments, and changes via voice or text directly from the calendar UI. The agent backend lives in a separate repo (`sally-schoolwork`), and this frontend provides the widget that connects to it.

## Related repos

- **Agent backend**: `sally-schoolwork` — LiveKit Agent with tools for grade/assignment queries. See its `PLAN.md` for full architecture.
- **Data repo**: `table-mutation-data` (private) — snapshot JSON files read by the agent at runtime.
- **This repo**: `table-mutation-tracker` — frontend widget that connects to the agent via LiveKit React SDK.

## Branch

This work is on the `feature/livekit-agent-widget` branch.

## Scope (Phase 5 of sally-schoolwork PLAN.md)

**Current scope (basic):**
- LiveKit React SDK integrated into the Next.js frontend
- Floating voice/text widget accessible from any page
- Connects to the Sally agent running on LiveKit Cloud

**Future scope:**
- Pass room metadata (selected date, class filter) to agent session for contextual queries
- Audio visualizer or avatar integration (Phase 6 of sally-schoolwork)

## Environment variables needed

```
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

These must be configured in:
- `.env.local` for local development
- Vercel project settings for production

## Architecture

```
Browser (Next.js on Vercel)
  └── AgentWidget component
        ├── Requests token from /api/livekit-token (server-side)
        ├── Connects to LiveKit room
        └── Sends voice/text to Sally agent (running on LiveKit Cloud)
              └── Agent reads local clone of table-mutation-data
```

The token endpoint is a Next.js API route that generates short-lived LiveKit access tokens server-side, keeping the API secret off the client.

## Files added/modified

```
frontend/
  app/api/livekit-token/route.ts  — New: server-side token endpoint
  components/AgentWidget.tsx       — New: floating voice/text widget
  app/layout.tsx                   — Modified: includes AgentWidget
  package.json                     — Modified: LiveKit SDK dependencies
```
