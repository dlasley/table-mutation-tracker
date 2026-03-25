"use client";

import { createContext, useContext, useState, useEffect, useRef } from "react";

const SuperUserContext = createContext(false);

export function useSuperUser() {
  return useContext(SuperUserContext);
}

export default function SuperUserProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [superUser, setSuperUser] = useState(false);
  const tapCount = useRef(0);
  const tapTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.metaKey && e.shiftKey && e.key.toLowerCase() === "s") {
        e.preventDefault();
        setSuperUser((v) => !v);
      }
    }
    function handleTap(e: Event) {
      const target = e.target as HTMLElement;
      if (!target.closest("[data-superuser-toggle]")) {
        tapCount.current = 0;
        return;
      }
      tapCount.current++;
      if (tapTimer.current) clearTimeout(tapTimer.current);
      if (tapCount.current >= 3) {
        tapCount.current = 0;
        e.preventDefault();
        setSuperUser((v) => !v);
      } else {
        tapTimer.current = setTimeout(() => {
          tapCount.current = 0;
        }, 500);
      }
    }
    window.addEventListener("keydown", handleKey);
    window.addEventListener("click", handleTap);
    return () => {
      window.removeEventListener("keydown", handleKey);
      window.removeEventListener("click", handleTap);
      if (tapTimer.current) clearTimeout(tapTimer.current);
    };
  }, []);

  return (
    <SuperUserContext.Provider value={superUser}>
      {children}
    </SuperUserContext.Provider>
  );
}
