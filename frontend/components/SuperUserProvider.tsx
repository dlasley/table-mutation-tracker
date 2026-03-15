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
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  return (
    <SuperUserContext.Provider value={superUser}>
      {children}
    </SuperUserContext.Provider>
  );
}
