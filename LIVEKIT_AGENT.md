# LiveKit Voice/Text Agent Integration

This document tracks the integration of a LiveKit voice/text agent widget into the table-mutation-tracker frontend.

## Overview

A LiveKit-powered agent ("Sally") allows users to ask questions about grades, assignments, and changes via voice or text directly from the calendar UI. The agent backend lives in a separate repo (`sally-schoolwork`), and this frontend provides the widget that connects to it.

## Related repos

- **Agent backend**: `sally-schoolwork` — LiveKit Agent with tools for grade/assignment queries. See its `PLAN.md` for full architecture and `PROGRESS.md` for current status.
- **Data repo**: `table-mutation-data` (private) — snapshot JSON files read by the agent at runtime.
- **This repo**: `table-mutation-tracker` — frontend widget that connects to the agent via LiveKit React SDK.

## Branch

This work is on the `feature/livekit-agent-widget` branch.

## Architecture

```
Browser (Next.js on Vercel)
  └── AgentWidget component
        ├── Generates stable device_id (localStorage UUID) for user profile tracking
        ├── Requests token from /api/livekit-token (server-side, passes device_id)
        ├── Connects to LiveKit room
        ├── Renders Hedra avatar video track (or BarVisualizer fallback)
        ├── NavigationHandler: receives RPC from agent, calls router.push()
        └── Sends voice/text to Sally agent (running on LiveKit Cloud)
              ├── Agent reads local clone of table-mutation-data
              ├── Agent tools auto-navigate browser via RPC
              └── Agent stores profiles/sessions in Supabase
```

## Environment variables

Set in `frontend/.env.local` for local development:

```
NEXT_PUBLIC_LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
```

## Frontend components

### AgentWidget (`frontend/components/AgentWidget.tsx`)
- Floating widget in bottom-right corner, accessible from any page
- Connect/disconnect with LiveKit room
- Renders Hedra avatar video when available, falls back to BarVisualizer
- `NavigationHandler` sub-component registers `navigateTo` RPC method
- `getDeviceId()` generates and persists a stable UUID in localStorage

### Token route (`frontend/app/api/livekit-token/route.ts`)
- Server-side JWT generation with `RoomAgentDispatch` for agent dispatch
- Accepts `participant_identity` (device_id) from the widget
- Keeps API secret off the client

### Navigation support
- `DayDetail.tsx` reads `?class=` query param to auto-select a class tab
- `page.tsx` (day route) preserves query params through the date→time redirect
- Agent tools navigate the browser as a side effect of data lookups (no explicit user request needed)

## Files added/modified

```
frontend/
  app/api/livekit-token/route.ts    — Server-side token endpoint
  components/AgentWidget.tsx         — Widget with video, audio, RPC navigation
  app/layout.tsx                     — AgentWidget in root layout
  app/day/[date]/page.tsx            — Query param preservation in redirect
  app/day/[date]/DayDetail.tsx       — ?class= param for tab selection
  package.json                       — LiveKit SDK dependencies
```
