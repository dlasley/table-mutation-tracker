"use client";

import LocalDate from "@/components/LocalDate";
import LocalTime from "@/components/LocalTime";

export default function LatestSnapshotLabel({ date, time }: { date: string; time: string }) {
  return (
    <h2 className="text-sm text-gray-500 text-center">
      Latest snapshot: <LocalDate time={time} date={date} />{" "}
      <LocalTime time={time} date={date} />
    </h2>
  );
}
