"use client";

import { useEffect, useState } from "react";

export function Clock() {
  const [time, setTime] = useState("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const dd = String(now.getDate()).padStart(2, '0');
      const mm = String(now.getMonth() + 1).padStart(2, '0'); // Enero es 0!
      const yyyy = now.getFullYear();
      
      const hh = String(now.getHours()).padStart(2, '0');
      const min = String(now.getMinutes()).padStart(2, '0');
      const ss = String(now.getSeconds()).padStart(2, '0');
      
      setTime(`${dd}/${mm}/${yyyy}|${hh}:${min}:${ss}`);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  if (!time) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "10px",
        left: "15px",
        fontFamily: "monospace",
        color: "#00ffff", // Cian electrico
        backgroundColor: "rgba(0, 0, 0, 0.6)",
        padding: "4px 8px",
        borderRadius: "4px",
        fontSize: "14px",
        zIndex: 9999,
        pointerEvents: "none"
      }}
    >
      {time}
    </div>
  );
}
