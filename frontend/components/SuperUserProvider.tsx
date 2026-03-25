"use client";

import { createContext, useContext, useState, useEffect, useRef, useCallback } from "react";

const SuperUserContext = createContext(false);
const ToggleRefContext = createContext<React.RefCallback<HTMLElement>>(() => {});

export function useSuperUser() {
  return useContext(SuperUserContext);
}

export function useSuperUserToggleRef() {
  return useContext(ToggleRefContext);
}

export default function SuperUserProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [superUser, setSuperUser] = useState(false);
  const tapCount = useRef(0);
  const tapTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  const toggleRef = useCallback((el: HTMLElement | null) => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
    if (!el) return;

    function handleTap() {
      tapCount.current++;
      if (tapTimer.current) clearTimeout(tapTimer.current);
      if (tapCount.current >= 3) {
        tapCount.current = 0;
        setSuperUser((v) => !v);
      } else {
        tapTimer.current = setTimeout(() => {
          tapCount.current = 0;
        }, 600);
      }
    }

    el.addEventListener("click", handleTap);
    cleanupRef.current = () => el.removeEventListener("click", handleTap);
  }, []);

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.metaKey && e.shiftKey && e.key.toLowerCase() === "s") {
        e.preventDefault();
        setSuperUser((v) => !v);
      }
    }
    window.addEventListener("keydown", handleKey);
    return () => {
      window.removeEventListener("keydown", handleKey);
      if (tapTimer.current) clearTimeout(tapTimer.current);
    };
  }, []);

  return (
    <SuperUserContext.Provider value={superUser}>
      <ToggleRefContext.Provider value={toggleRef}>
        {children}
      </ToggleRefContext.Provider>
    </SuperUserContext.Provider>
  );
}
