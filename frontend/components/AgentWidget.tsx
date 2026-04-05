"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  useRoomContext,
  BarVisualizer,
  DisconnectButton,
  VideoTrack,
} from "@livekit/components-react";
import "@livekit/components-styles";

const LIVEKIT_URL = process.env.NEXT_PUBLIC_LIVEKIT_URL || "";

interface ConnectionDetails {
  serverUrl: string;
  participantToken: string;
}

function NavigationHandler() {
  const room = useRoomContext();
  const router = useRouter();

  useEffect(() => {
    const handler = async (data: { payload: string }) => {
      const { view, date, className } = JSON.parse(data.payload);
      if (className === "help") {
        router.push("/help");
      } else if (view === "calendar") {
        router.push("/");
      } else if (date) {
        const classParam = className ? `?class=${className}` : "";
        router.push(`/day/${date}${classParam}`);
      }
      return JSON.stringify({ ok: true });
    };

    room.localParticipant.registerRpcMethod("navigateTo", handler);

    return () => {
      room.localParticipant.unregisterRpcMethod("navigateTo");
    };
  }, [room, router]);

  return null;
}

function AgentPanel() {
  const { state, audioTrack, videoTrack } = useVoiceAssistant();

  const stateLabel: Record<string, string> = {
    disconnected: "Disconnected",
    connecting: "Connecting...",
    initializing: "Starting up...",
    listening: "Listening",
    thinking: "Thinking...",
    speaking: "Speaking",
  };

  return (
    <div className="flex flex-col items-center gap-3 p-4">
      {videoTrack ? (
        <div className="w-full aspect-square rounded overflow-hidden bg-black">
          <VideoTrack
            trackRef={videoTrack}
            className="w-full h-full object-cover"
          />
        </div>
      ) : (
        <div className="w-full h-16">
          <BarVisualizer
            state={state}
            barCount={5}
            trackRef={audioTrack}
            className="w-full h-full"
          />
        </div>
      )}
      <p className="text-xs text-gray-500 dark:text-gray-400">
        {stateLabel[state] || state}
      </p>
      <DisconnectButton className="px-3 py-1.5 text-xs rounded bg-red-500 hover:bg-red-600 text-white transition-colors">
        Disconnect
      </DisconnectButton>
      <RoomAudioRenderer />
    </div>
  );
}

function getDeviceId(): string {
  const key = "sally_device_id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(key, id);
  }
  return id;
}

const PERSONAS = [
  { value: "avatar1", label: "Human 1" },
  { value: "avatar2", label: "Freyja" },
  { value: "avatar3", label: "Human 2" },
];

export default function AgentWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [connectionDetails, setConnectionDetails] =
    useState<ConnectionDetails | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedPersona, setSelectedPersona] = useState("avatar2");

  const connect = useCallback(async () => {
    setError(null);
    try {
      const response = await fetch("/api/livekit-token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          participant_identity: getDeviceId(),
          participant_metadata: JSON.stringify({ persona: selectedPersona }),
          room_config: {
            agents: [{ agent_name: "my-agent" }],
          },
        }),
      });

      if (!response.ok) {
        setError("Connection failed. Try again.");
        return;
      }

      const data = await response.json();
      setConnectionDetails({
        serverUrl: data.server_url,
        participantToken: data.participant_token,
      });
    } catch {
      setError("Connection failed. Try again.");
    }
  }, [selectedPersona]);

  const disconnect = useCallback(() => {
    setConnectionDetails(null);
  }, []);

  if (!LIVEKIT_URL) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {isOpen && (
        <div className="mb-2 w-72 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg overflow-hidden">
          <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
            <span className="text-sm font-medium">Sally</span>
            <button
              onClick={() => {
                disconnect();
                setIsOpen(false);
              }}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-lg leading-none"
              aria-label="Close"
            >
              &times;
            </button>
          </div>

          {connectionDetails ? (
            <LiveKitRoom
              serverUrl={connectionDetails.serverUrl}
              token={connectionDetails.participantToken}
              connect={true}
              audio={true}
              onDisconnected={disconnect}
            >
              <NavigationHandler />
              <AgentPanel />
            </LiveKitRoom>
          ) : (
            <div className="flex flex-col items-center gap-3 p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                Ask Sally about your grades, assignments, and changes.
              </p>
              <select
                value={selectedPersona}
                onChange={(e) => setSelectedPersona(e.target.value)}
                className="w-full px-3 py-1.5 text-sm rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300"
              >
                {PERSONAS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
              {error && (
                <p className="text-xs text-red-500">{error}</p>
              )}
              <button
                onClick={connect}
                className="px-4 py-2 text-sm rounded-md bg-blue-600 hover:bg-blue-700 text-white transition-colors"
              >
                Start conversation
              </button>
            </div>
          )}
        </div>
      )}

      <button
        onClick={() => setIsOpen(!isOpen)}
        className="px-3 py-2 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg text-sm font-medium transition-colors"
        aria-label={isOpen ? "Close Sally" : "Talk to Sally"}
      >
        {isOpen ? <span>&times;</span> : "Sally Schoolwork"}
      </button>
    </div>
  );
}
