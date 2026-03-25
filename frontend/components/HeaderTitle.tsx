"use client";

import { useSuperUserToggleRef } from "@/components/SuperUserProvider";

export default function HeaderTitle() {
  const toggleRef = useSuperUserToggleRef();

  return (
    <span ref={toggleRef} className="text-lg font-semibold select-none cursor-default">
      Grades
    </span>
  );
}
