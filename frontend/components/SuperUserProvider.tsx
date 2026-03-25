"use client";

import { createContext, useContext, useState, useEffect } from "react";

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

  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if (e.metaKey && e.shiftKey && e.key.toLowerCase() === "s") {
        e.preventDefault();
        setSuperUser((v) => !v);
      }
    }
    function handleClick(e: MouseEvent) {
      if (e.detail === 3) {
        const target = e.target as HTMLElement;
        if (target.closest("[data-superuser-toggle]")) {
          e.preventDefault();
          setSuperUser((v) => !v);
        }
      }
    }
    window.addEventListener("keydown", handleKey);
    window.addEventListener("click", handleClick);
    return () => {
      window.removeEventListener("keydown", handleKey);
      window.removeEventListener("click", handleClick);
    };
  }, []);

  return (
    <SuperUserContext.Provider value={superUser}>
      {children}
    </SuperUserContext.Provider>
  );
}
