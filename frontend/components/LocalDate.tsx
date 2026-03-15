"use client";

import { useState, useEffect } from "react";
import { toLocalDate } from "@/lib/format";

/** Renders a UTC date+time as the browser's local YYYY-MM-DD date. Only converts after mount to avoid SSR hydration mismatch. */
export default function LocalDate({ time, date }: { time: string; date: string }) {
  const [display, setDisplay] = useState(date);

  useEffect(() => {
    setDisplay(toLocalDate(date, time));
  }, [time, date]);

  return <>{display}</>;
}
