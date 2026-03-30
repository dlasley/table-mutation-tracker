"use client";

import { useCallback, useState } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
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

export default function AgentWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [connectionDetails, setConnectionDetails] =
    useState<ConnectionDetails | null>(null);

  const connect = useCallback(async () => {
    const response = await fetch("/api/livekit-token", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_config: {
          agents: [{ agent_name: "my-agent" }],
        },
      }),
    });

    if (!response.ok) {
      console.error("Failed to get token:", await response.text());
      return;
    }

    const data = await response.json();
    setConnectionDetails({
      serverUrl: data.server_url,
      participantToken: data.participant_token,
    });
  }, []);

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
              <AgentPanel />
            </LiveKitRoom>
          ) : (
            <div className="flex flex-col items-center gap-3 p-6">
              <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
                Ask Sally about your grades, assignments, and changes.
              </p>
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
        className="w-12 h-12 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg flex items-center justify-center transition-colors"
        aria-label={isOpen ? "Close Sally" : "Talk to Sally"}
      >
        {isOpen ? (
          <span className="text-lg">&times;</span>
        ) : (
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-6 h-6"
          >
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10h5v-2h-5c-4.34 0-8-3.66-8-8s3.66-8 8-8 8 3.66 8 8v1.43c0 .79-.71 1.57-1.5 1.57s-1.5-.78-1.5-1.57V12c0-2.76-2.24-5-5-5s-5 2.24-5 5 2.24 5 5 5c1.38 0 2.64-.56 3.54-1.47.65.89 1.77 1.47 2.96 1.47 1.97 0 3.5-1.6 3.5-3.57V12c0-5.52-4.48-10-10-10zm0 13c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z" />
          </svg>
        )}
      </button>
    </div>
  );
}
