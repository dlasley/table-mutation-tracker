"use client";

import { useState, useEffect } from "react";

const STORAGE_KEY = "change-legend-dismissed";

export default function ChangeLegend() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      setVisible(true);
    }
  }, []);

  if (!visible) return null;

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, "1");
    setVisible(false);
  }

  return (
    <div className="rounded border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950/40 px-4 py-3 text-sm flex items-start gap-3">
      <div className="flex-1 space-y-1">
        <div className="font-medium text-blue-800 dark:text-blue-300 mb-1.5">Reading change indicators</div>
        <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs">
          <span><span className="text-green-600 dark:text-green-400 font-mono font-bold">+</span> New assignment</span>
          <span><span className="text-orange-500 font-mono font-bold">~</span> Score or grade changed</span>
          <span><span className="text-red-500 font-mono font-bold">-</span> Assignment removed</span>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Click a highlighted row to see what changed.</div>
      </div>
      <button
        onClick={dismiss}
        className="text-blue-400 hover:text-blue-600 dark:hover:text-blue-300 text-lg leading-none mt-0.5"
        title="Dismiss"
      >
        &times;
      </button>
    </div>
  );
}
