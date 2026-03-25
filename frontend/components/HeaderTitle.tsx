"use client";

import { useSuperUserToggleRef } from "@/components/SuperUserProvider";

export default function HeaderTitle() {
  const toggleRef = useSuperUserToggleRef();

  return (
    <a href="/" ref={toggleRef} className="text-lg font-semibold select-none">
      Grades
    </a>
  );
}
