"use client";

import { useState, useEffect } from "react";
import { formatTime } from "@/lib/format";

/** Renders UTC time in the browser's local timezone. Only formats after mount to avoid SSR hydration mismatch. */
export default function LocalTime({ time, date }: { time: string; date: string }) {
  const [display, setDisplay] = useState(formatTime(time));

  useEffect(() => {
    setDisplay(formatTime(time, date));
  }, [time, date]);

  return <>{display}</>;
}
