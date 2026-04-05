import { NextRequest, NextResponse } from "next/server";
import { AccessToken } from "livekit-server-sdk";
import { RoomAgentDispatch, RoomConfiguration } from "@livekit/protocol";

export async function POST(request: NextRequest) {
  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const serverUrl = process.env.LIVEKIT_URL;

  if (!apiKey || !apiSecret || !serverUrl) {
    return NextResponse.json(
      { error: "LiveKit credentials not configured" },
      { status: 500 }
    );
  }

  try {
    const body = await request.json().catch(() => ({}));

    const roomName = body.room_name || `grades-${Date.now()}`;
    const participantIdentity =
      body.participant_identity || `user-${Date.now()}`;
    const participantName = body.participant_name || "Student";
    const roomConfig = body.room_config;

    const ip =
      request.headers.get("x-forwarded-for")?.split(",")[0].trim() ||
      request.headers.get("x-real-ip") ||
      "unknown";

    const at = new AccessToken(apiKey, apiSecret, {
      identity: participantIdentity,
      name: participantName,
      metadata: body.participant_metadata || "",
      attributes: { ...(body.participant_attributes || {}), ip_address: ip },
      ttl: "10m",
    });

    at.addGrant({
      roomJoin: true,
      room: roomName,
      canPublish: true,
      canSubscribe: true,
    });

    if (roomConfig) {
      const rc = new RoomConfiguration();
      if (roomConfig.agents) {
        rc.agents = roomConfig.agents.map(
          (a: { agent_name: string; metadata?: string }) =>
            new RoomAgentDispatch({
              agentName: a.agent_name,
              metadata: a.metadata || "",
            })
        );
      }
      at.roomConfig = rc;
    }

    const participantToken = await at.toJwt();

    return NextResponse.json(
      {
        server_url: serverUrl,
        participant_token: participantToken,
      },
      { status: 201 }
    );
  } catch {
    return NextResponse.json(
      { error: "Failed to generate token" },
      { status: 500 }
    );
  }
}
