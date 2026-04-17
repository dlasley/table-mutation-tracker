# LiveKit Agent Widget - Progress

## Branch
Merged to `main` (2026-04-14)

## Status
Integrated and deployed. Widget live on production frontend.

## Completed Work

### Post-merge updates (2026-04-15/16)
- AgentWidget: superuser triple-tap on widget header toggles persona selector (public "Sally Schoolwork" vs private avatar options)
- AgentWidget: /deleted route added to NavigationHandler RPC dispatch
- Token route: rate limiting (10 req/min per IP) to prevent token abuse
- help/page.tsx: NavBadge annotations showing which queries navigate the browser, Comparisons section, additional question examples
- LIVEKIT_AGENT.md: RPC contract location documented (`sally-schoolwork/docs/CONTRACTS.md`)

### Initial integration (2026-03-30)
- LiveKit React SDK integrated (livekit-client, @livekit/components-react, livekit-server-sdk, @livekit/protocol)
- Token API route with RoomAgentDispatch for agent dispatch
- AgentWidget with video track rendering (Hedra avatar) and BarVisualizer fallback
- Stable device_id via localStorage UUID for user profile tracking
- NavigationHandler: agent can navigate the browser via LiveKit RPC
- DayDetail reads `?class=` query param for class tab deep-linking
- Day page redirect preserves query params through date→time redirect

## Files added/modified
```
frontend/
  app/api/livekit-token/route.ts    — Token endpoint with agent dispatch + rate limiting
  components/AgentWidget.tsx         — Widget: video/audio, connect/disconnect, RPC navigation, superuser persona selector
  app/layout.tsx                     — AgentWidget added to root layout
  app/day/[date]/page.tsx            — Redirect preserves query params
  app/day/[date]/DayDetail.tsx       — Reads ?class= param for tab selection
  app/help/page.tsx                  — Agent capabilities with NavBadge annotations
  package.json                       — LiveKit SDK dependencies
LIVEKIT_AGENT.md                     — Integration documentation
PROGRESS_LIVEKIT.md                  — This file
```

## Known Issues
- Navigation mismatch: agent narrates aggregate data but browser shows single snapshot diff view. Tracked in sally-schoolwork.

## Next Steps
- Code review and refactoring (see sally-schoolwork PROGRESS.md)
- End-to-end test with LiveKit Cloud credentials configured
