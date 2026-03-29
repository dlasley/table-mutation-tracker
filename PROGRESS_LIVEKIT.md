# LiveKit Agent Widget - Progress

## Branch
`feature/livekit-agent-widget`

## Last Session Summary
**Date**: 2026-03-29

### Completed Work
- Installed LiveKit React SDK dependencies (`livekit-client`, `@livekit/components-react`, `@livekit/components-styles`, `livekit-server-sdk`, `@livekit/protocol`)
- Created token API route (`frontend/app/api/livekit-token/route.ts`) — server-side JWT generation with agent dispatch
- Created AgentWidget component (`frontend/components/AgentWidget.tsx`) — floating widget with connect/disconnect, BarVisualizer, and state display
- Added AgentWidget to root layout (`frontend/app/layout.tsx`)
- Created `LIVEKIT_AGENT.md` — full integration documentation
- Updated `CLAUDE.md` with cross-reference to LiveKit work
- Build succeeds, no new lint errors

## Uncommitted Changes
- `frontend/app/api/livekit-token/route.ts` — New
- `frontend/components/AgentWidget.tsx` — New
- `frontend/app/layout.tsx` — Modified (AgentWidget added)
- `frontend/package.json` — Modified (LiveKit dependencies)
- `frontend/package-lock.json` — Modified
- `LIVEKIT_AGENT.md` — New
- `CLAUDE.md` — Modified (cross-reference)
- `PROGRESS_LIVEKIT.md` — New

## Status
- [x] Configure LiveKit Cloud credentials in `.env.local` and `frontend/.env.local`
- [x] Deploy Sally agent from `sally-schoolwork` to LiveKit Cloud
- [x] End-to-end test: frontend widget connects to agent via LiveKit Cloud
- [x] Fixed token route agent dispatch (RoomAgentDispatch)

## Next Steps
- Phase 6: Voice/persona tuning, avatar, visualizer
- Merge `feature/livekit-agent-widget` into main when ready
