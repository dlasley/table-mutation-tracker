# LiveKit Agent Widget - Progress

## Branch
`feature/livekit-agent-widget`

## Last Session Summary
**Date**: 2026-03-30

### Completed Work
- LiveKit React SDK integrated (livekit-client, @livekit/components-react, livekit-server-sdk, @livekit/protocol)
- Token API route with RoomAgentDispatch for agent dispatch
- AgentWidget with video track rendering (Hedra avatar) and BarVisualizer fallback
- Stable device_id via localStorage UUID for user profile tracking
- NavigationHandler: agent can navigate the browser via LiveKit RPC
- DayDetail reads `?class=` query param for class tab deep-linking
- Day page redirect preserves query params through date→time redirect
- End-to-end working: voice + avatar + tools + browser navigation

### Commits on this branch
- `30ee86d` — Initial widget (token route, AgentWidget, layout)
- `522f84a` — Avatar video track rendering
- `fa6a3af` — Stable device_id in token request
- `01e3886` — Agent-driven browser navigation (RPC handler, class param, redirect fix)

## Files modified/added
```
frontend/
  app/api/livekit-token/route.ts    — Token endpoint with agent dispatch
  components/AgentWidget.tsx         — Widget: video/audio, connect/disconnect, RPC navigation
  app/layout.tsx                     — AgentWidget added to root layout
  app/day/[date]/page.tsx            — Redirect preserves query params
  app/day/[date]/DayDetail.tsx       — Reads ?class= param for tab selection
  package.json                       — LiveKit SDK dependencies
LIVEKIT_AGENT.md                     — Integration documentation
PROGRESS_LIVEKIT.md                  — This file
```

## Known Issues
- Navigation mismatch: agent narrates aggregate data but browser shows single snapshot diff
- Needs code review to align tool output with what the frontend renders at each route

## Next Steps
- Code review and refactoring (see sally-schoolwork PROGRESS.md for full list)
- Merge `feature/livekit-agent-widget` into main when review is complete
